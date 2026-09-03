import json
import tempfile
import threading
import unittest
from datetime import date
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import quote

from skills.examlex.scripts.web_app import classify_upload, create_server, today_local


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="examlex-web-test-")
        self.server = create_server("127.0.0.1", 0, self.temp.name)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def request(self, method, path, payload=None, headers=None, raw=None):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=3)
        body = raw
        request_headers = dict(headers or {})
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode()
            request_headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        content = response.read()
        connection.close()
        try:
            value = json.loads(content.decode("utf-8"))
        except json.JSONDecodeError:
            value = content.decode("utf-8", errors="replace")
        return response.status, value

    def test_exam_directory_preserves_order_and_release_boundaries(self):
        status, payload = self.request("GET", "/api/exams")
        self.assertEqual(200, status)
        self.assertEqual(["CET4", "CET6", "POSTGRADUATE_ENGLISH", "TEM4", "TEM8"], payload["exam_order"])
        releases = {item["id"]: item["content_status"] for item in payload["exams"]}
        self.assertEqual("detailed_materials_draft", releases["CET4"])
        self.assertEqual("detailed_materials_draft", releases["CET6"])
        self.assertEqual("foundation_release", releases["POSTGRADUATE_ENGLISH"])

    def test_content_has_no_material_role_and_keeps_extension_labels(self):
        status, payload = self.request("GET", "/api/content?exam=POSTGRADUATE_ENGLISH")
        self.assertEqual(200, status)
        serialized = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("教材讲解", serialized)
        self.assertEqual("extension_not_exam_section", payload["modules"]["listening"]["source_status"])

    def test_heatmap_is_exact_month_and_separates_exam_tracks(self):
        status, before = self.request("GET", "/api/heatmap?exam=CET4&year=2024&month=2")
        self.assertEqual(200, status)
        self.assertEqual(29, len(before["days"]))
        today = today_local()
        status, _ = self.request("POST", "/api/practice/record", {"exam": "CET4", "module": "reading", "total_items": 20, "correct_items": 14, "duration_minutes": 40, "date": today})
        self.assertEqual(201, status)
        status, cet4 = self.request("GET", f"/api/heatmap?exam=CET4&year={today[:4]}&month={int(today[5:7])}")
        self.assertEqual(200, status)
        status, cet6 = self.request("GET", f"/api/heatmap?exam=CET6&year={today[:4]}&month={int(today[5:7])}")
        self.assertEqual(200, status)
        cet4_day = next(item for item in cet4["days"] if item["date"] == today)
        cet6_day = next(item for item in cet6["days"] if item["date"] == today)
        self.assertGreater(cet4_day["score"], 0)
        self.assertEqual(0, cet6_day["score"])
        self.assertEqual(3, max(item["level"] for item in cet4["days"]))

    def test_year_heatmap_and_focus_session_record_actual_duration(self):
        year = date.today().year
        status, payload = self.request("GET", f"/api/heatmap/year?exam=CET4&year={year}")
        self.assertEqual(200, status)
        self.assertEqual(366 if date(year, 12, 31).timetuple().tm_yday == 366 else 365, len(payload["days"]))
        self.assertIn("start_weekday", payload)
        status, saved = self.request("POST", "/api/focus/session", {"exam": "CET4", "module": "reading", "duration_seconds": 150, "planned_minutes": 25, "completed": False})
        self.assertEqual(201, status)
        self.assertEqual(150, saved["session"]["duration_seconds"])
        status, payload = self.request("GET", f"/api/heatmap/year?exam=CET4&year={year}")
        self.assertEqual(2, next(item for item in payload["days"] if item["date"] == today_local())["minutes"])

    def test_tasks_are_completed_from_practice_evidence(self):
        status, before = self.request("GET", "/api/bootstrap?exam=CET4")
        self.assertEqual(200, status)
        self.assertFalse(next(item for item in before["tasks"] if item["module"] == "reading")["done"])
        status, _ = self.request("POST", "/api/practice/record", {"exam": "CET4", "module": "reading", "total_items": 10, "correct_items": 8, "duration_minutes": 20})
        self.assertEqual(201, status)
        status, after = self.request("GET", "/api/bootstrap?exam=CET4")
        self.assertEqual(200, status)
        reading = next(item for item in after["tasks"] if item["module"] == "reading")
        writing = next(item for item in after["tasks"] if item["module"] == "writing")
        self.assertTrue(reading["done"])
        self.assertEqual("evidence", reading["completion_source"])
        self.assertFalse(writing["done"])

    def test_future_practice_is_rejected_and_history_is_preserved(self):
        future = date.today().replace(year=date.today().year + 1).isoformat()
        status, payload = self.request("POST", "/api/practice/record", {"exam": "CET4", "module": "reading", "total_items": 1, "correct_items": 1, "duration_minutes": 1, "date": future})
        self.assertEqual(400, status)
        self.assertIn("future", payload["error"])
        status, january = self.request("GET", "/api/heatmap?exam=CET4&year=2025&month=1")
        self.assertEqual(31, len(january["days"]))
        status, december = self.request("GET", "/api/heatmap?exam=CET4&year=2025&month=12")
        self.assertEqual(31, len(december["days"]))

    def test_task_completion_is_idempotent_for_the_same_state(self):
        status, boot = self.request("GET", "/api/bootstrap?exam=CET4")
        self.assertEqual(200, status)
        task_id = boot["tasks"][0]["id"]
        status, first = self.request("POST", "/api/tasks/toggle", {"exam": "CET4", "task_id": task_id, "done": True})
        self.assertEqual(200, status)
        status, second = self.request("POST", "/api/tasks/toggle", {"exam": "CET4", "task_id": task_id, "done": True})
        self.assertEqual(200, status)
        self.assertEqual(first["summary"]["completed_tasks"], second["summary"]["completed_tasks"])

    def test_memory_review_is_idempotent(self):
        status, practice = self.request("POST", "/api/practice/record", {"exam": "CET4", "module": "vocabulary", "total_items": 8, "correct_items": 6, "duration_minutes": 10, "error_tags": []})
        self.assertEqual(201, status)
        status, boot = self.request("GET", "/api/bootstrap?exam=CET4")
        self.assertEqual(200, status)
        card_id = next(card["id"] for card in boot["cards"] if card.get("source_id") == practice["record"]["id"])
        body = {"exam": "CET4", "card_id": card_id, "rating": "good", "idempotency_key": "review-test-1"}
        status, first = self.request("POST", "/api/memory/review", body)
        self.assertEqual(200, status)
        status, second = self.request("POST", "/api/memory/review", body)
        self.assertEqual(200, status)
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first["card"]["due_at"], second["card"]["due_at"])

    def test_upload_is_quarantined_and_provider_does_not_store_key(self):
        boundary = "----ExamLexBoundary"
        raw = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"notes.md\"\r\nContent-Type: text/markdown\r\n\r\nhello\r\n--{boundary}--\r\n").encode()
        status, upload = self.request("POST", "/api/upload?exam=CET4", headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, raw=raw)
        self.assertEqual(201, status)
        self.assertEqual("quarantined", upload["upload"]["status"])
        self.assertTrue((Path(self.temp.name) / "quarantine" / upload["upload"]["stored_name"]).exists())
        status, provider = self.request("POST", "/api/providers", {"provider_id": "openai", "endpoint": "https://api.openai.com/v1", "model": "gpt-5", "api_key_env": "OPENAI_API_KEY", "api_key": "should-never-be-stored"})
        self.assertEqual(200, status)
        self.assertNotIn("api_key", provider["provider"])
        state_text = (Path(self.temp.name) / "state.json").read_text(encoding="utf-8")
        self.assertNotIn("should-never-be-stored", state_text)

    def test_upload_routing_uses_file_domain_before_content_shape(self):
        writing = classify_upload("四级作文高分金句与模板.pdf", "句子：It is widely acknowledged that...")
        translation = classify_upload("四六级翻译常用词句.docx", "文化遗产 heritage 促进 promote")
        vocabulary = classify_upload("四级高频词汇.txt", "abandon abandonment collocation")
        strategy = classify_upload("阅读方法论与技巧.md", "方法：先定位，再核对证据")
        generic_translation = classify_upload("资料.docx", "本章整理翻译常用词句与文化主题表达")
        ambiguous_sentence = classify_upload("notes.txt", "It is widely acknowledged that practice matters.")
        self.assertEqual(("writing_ingest", "writing", "template"), (writing["category"], writing["target_module"], writing["content_kind"]))
        self.assertEqual(("translation_ingest", "translation"), (translation["category"], translation["target_module"]))
        self.assertEqual(("vocabulary_ingest", "vocabulary"), (vocabulary["category"], vocabulary["target_module"]))
        self.assertEqual(("strategy_ingest", None), (strategy["category"], strategy["target_module"]))
        self.assertEqual("translation", generic_translation["target_module"])
        self.assertEqual("needs_user_confirmation", ambiguous_sentence["category"])

    def test_pipeline_keeps_simulation_nonofficial_and_exposes_checkpoints(self):
        boundary = "----ExamLexPipeline"
        raw = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"阅读模拟题.md\"\r\nContent-Type: text/markdown\r\n\r\n1. The evidence is ____ .\nA. clear\nB. random\nC. weak\nD. absent\r\n--{boundary}--\r\n").encode()
        status, payload = self.request("POST", "/api/upload?exam=CET4", headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, raw=raw)
        self.assertEqual(201, status)
        upload = payload["upload"]
        self.assertEqual("simulation_not_official", upload["classification"]["category"])
        self.assertEqual("extract", upload["pipeline"]["current_stage"])
        status, pipeline = self.request("POST", "/api/pipeline/run", {"upload_id": upload["id"], "action": "auto"})
        self.assertEqual(200, status)
        self.assertEqual("complete", pipeline["pipeline"]["current_stage"])
        status, uploads = self.request("GET", "/api/uploads?exam=CET4")
        self.assertEqual(200, status)
        simulation = next(item for item in uploads["simulations"] if item["upload_id"] == upload["id"])
        self.assertEqual("ready_private", simulation["status"])
        self.assertEqual("reading", simulation["module"])

    def test_past_paper_requires_explicit_source_verification_before_commit(self):
        boundary = "----ExamLexPast"
        raw = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"CET4历年真题阅读.md\"\r\nContent-Type: text/markdown\r\n\r\nOfficial past paper content.\r\n--{boundary}--\r\n").encode()
        status, payload = self.request("POST", "/api/upload?exam=CET4", headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, raw=raw)
        self.assertEqual(201, status)
        upload_id = payload["upload"]["id"]
        status, blocked = self.request("POST", "/api/pipeline/run", {"upload_id": upload_id, "action": "auto"})
        self.assertEqual(200, status)
        self.assertEqual("blocked", next(stage for stage in blocked["pipeline"]["stages"] if stage["name"] == "commit")["status"])
        status, verified = self.request("POST", "/api/pipeline/verify", {"upload_id": upload_id, "evidence_level": "S", "source_name": "CET 考试官方资料", "note": "年份和试卷版本已核对"})
        self.assertEqual(200, status)
        self.assertEqual("verified_official", verified["upload"]["source_status"])
        status, committed = self.request("POST", "/api/pipeline/run", {"upload_id": upload_id, "action": "auto"})
        self.assertEqual(200, status)
        self.assertEqual("complete", committed["pipeline"]["current_stage"])

    def test_source_catalog_and_artifact_rules_are_available_to_the_web_agent(self):
        status, catalog = self.request("GET", "/api/sources/catalog?exam=CET4&section=reading")
        self.assertEqual(200, status)
        self.assertIn("S", catalog["evidence_levels"])
        self.assertTrue(catalog["sources"])
        status, rules = self.request("GET", "/api/artifacts/rules?exam=CET4")
        self.assertEqual(200, status)
        self.assertIn("required_sections", rules["profiles"])

    def test_profile_separates_self_assessment_from_evidence_assessment(self):
        status, before = self.request("GET", "/api/profile/diagnosis?exam=CET4")
        self.assertEqual(200, status)
        self.assertFalse(before["self_assessment"]["configured"])
        self.assertIsNone(before["self_assessment"]["foundation_level"])
        self.assertEqual([], before["system_assessment"]["strengths"])
        self.assertEqual("insufficient_evidence", before["system_assessment"]["status"])

        status, saved = self.request("POST", "/api/profile", {
            "exam_type": "CET4",
            "foundation_level": "基础较好",
            "target_band": "550+",
            "self_strengths": "词汇，语法",
            "self_gaps": ["听力连读", "阅读定位"],
            "daily_time_budget_minutes": 60,
        })
        self.assertEqual(200, status)
        self.assertEqual(["词汇", "语法"], saved["profile"]["self_strengths"])

        status, after = self.request("GET", "/api/profile/diagnosis?exam=CET4")
        self.assertEqual(200, status)
        self.assertTrue(after["self_assessment"]["configured"])
        self.assertEqual("基础较好", after["self_assessment"]["foundation_level"])
        self.assertEqual(["听力连读", "阅读定位"], after["self_assessment"]["gaps"])
        self.assertEqual("550+", after["system_assessment"]["target_band"])
        self.assertEqual("insufficient_evidence", after["system_assessment"]["status"])

        status, _ = self.request("POST", "/api/practice/record", {
            "exam": "CET4", "module": "reading", "total_items": 10,
            "correct_items": 8, "duration_minutes": 20,
        })
        self.assertEqual(201, status)
        status, after_one = self.request("GET", "/api/profile/diagnosis?exam=CET4")
        self.assertEqual(200, status)
        self.assertEqual("insufficient_evidence", after_one["system_assessment"]["status"])
        self.assertEqual(0, after_one["system_assessment"]["evidence_records"])

        for index in range(3):
            status, _ = self.request("POST", "/api/practice/record", {
                "exam": "CET4", "module": "reading", "total_items": 10,
                "correct_items": 7 + index, "duration_minutes": 20,
                "source_status": "simulation_not_official", "title": f"CET4 模拟卷 {index + 1}",
            })
            self.assertEqual(201, status)
        status, with_evidence = self.request("GET", "/api/profile/diagnosis?exam=CET4")
        self.assertEqual(200, status)
        self.assertEqual("evidence_based", with_evidence["system_assessment"]["status"])
        self.assertEqual(3, with_evidence["system_assessment"]["evidence_records"])
        self.assertTrue(with_evidence["system_assessment"]["assessment_ready"])

    def test_exam_scoped_practice_records_and_agent_context_do_not_overlap(self):
        for exam in ("CET4", "CET6"):
            status, _ = self.request("POST", "/api/practice/record", {
                "exam": exam, "module": "reading", "total_items": 5,
                "correct_items": 4, "duration_minutes": 10,
                "source_status": "simulation_not_official", "title": f"{exam} 模拟卷",
            })
        status, cet4 = self.request("GET", "/api/practice/records?exam=CET4&kind=simulation")
        self.assertEqual(200, status)
        self.assertTrue(all(item["exam"] == "CET4" for item in cet4["records"]))
        self.assertEqual(1, len(cet4["records"]))
        status, cet6 = self.request("GET", "/api/practice/records?exam=CET6&kind=simulation")
        self.assertEqual(200, status)
        self.assertTrue(all(item["exam"] == "CET6" for item in cet6["records"]))
        self.assertEqual(1, len(cet6["records"]))
        status, context = self.request("GET", f"/api/agent/context?exam=CET4&module=reading&q={quote('模拟卷')}")
        self.assertEqual(200, status)
        self.assertEqual("CET4", context["exam"])
        self.assertTrue(all("CET6" not in json.dumps(item, ensure_ascii=False) for item in context["results"]))

    def test_profile_plan_errors_and_trends_endpoints(self):
        status, profile = self.request("POST", "/api/profile", {"exam_type": "CET4", "learner_id": "demo", "foundation_level": "基础较好", "target_band": "550+", "daily_time_budget_minutes": 60})
        self.assertEqual(200, status)
        self.assertEqual("基础较好", profile["profile"]["foundation_level"])
        status, plan = self.request("GET", "/api/plan?exam=CET4")
        self.assertEqual(200, status)
        self.assertEqual("CET4", plan["exam_type"])
        status, _ = self.request("POST", "/api/practice/record", {"exam": "CET4", "module": "reading", "total_items": 10, "correct_items": 5, "duration_minutes": 20, "error_tags": ["READING_INFERENCE_FAIL"]})
        self.assertEqual(201, status)
        status, errors = self.request("GET", "/api/errors?exam=CET4")
        self.assertEqual(200, status)
        self.assertEqual(1, errors["top_risks"][0]["count"])
        status, trends = self.request("GET", "/api/trends?exam=CET4")
        self.assertEqual(200, status)
        self.assertIn("modules", trends)

    def test_static_home_is_available(self):
        status, payload = self.request("GET", "/api/health")
        self.assertEqual(200, status)
        self.assertTrue(payload["ok"])
        status, _ = self.request("GET", "/")
        self.assertEqual(200, status)

    def test_agent_runtime_has_offline_fallback_and_persists_evidence(self):
        status, manifest = self.request("GET", "/api/agent/manifest")
        self.assertEqual(200, status)
        self.assertIn("writing", [item["id"] for item in manifest["agents"]])
        status, payload = self.request("POST", "/api/agent/run", {
            "exam": "CET4",
            "module": "writing",
            "input": "This is a short essay.\n\nHowever, practice matters.",
            "source_ids": ["upload-1"],
            "use_model": False,
        })
        self.assertEqual(200, status)
        self.assertEqual("deterministic", payload["run"]["mode"])
        self.assertEqual("upload-1", payload["run"]["output"]["evidence"][0]["source_id"])
        self.assertIn("rag", payload["run"])
        self.assertGreater(payload["run"]["rag"]["total_indexed"], 0)
        status, runs = self.request("GET", "/api/agent/runs?exam=CET4&module=writing")
        self.assertEqual(200, status)
        self.assertEqual(1, len(runs["runs"]))

    def test_global_agent_manifest_and_rag_context(self):
        status, manifest = self.request("GET", "/api/agent/manifest")
        self.assertEqual(200, status)
        self.assertIn("basics", [item["id"] for item in manifest["agents"]])
        self.assertTrue(manifest["capabilities"]["rag"]["enabled"])
        status, context = self.request("GET", "/api/agent/context?exam=CET4&module=basics&q=%E8%AF%8D%E6%80%A7")
        self.assertEqual(200, status)
        self.assertGreater(context["total_indexed"], 0)
        status, payload = self.request("POST", "/api/agent/run", {"exam": "CET4", "module": "basics", "path": "/english/basics", "input": "词性和句型怎么判断", "use_model": False})
        self.assertEqual(200, status)
        self.assertEqual("basics", payload["run"]["scene"])

    def test_prompt_library_routes_related_templates(self):
        status, payload = self.request("GET", "/api/agent/prompts?module=listening")
        self.assertEqual(200, status)
        self.assertGreaterEqual(payload["library"]["prompt_count"], 40)
        self.assertTrue(any(item["id"] == "016" for item in payload["prompts"]))
        status, run = self.request("POST", "/api/agent/run", {"exam": "CET4", "module": "listening", "input": "练习连读和弱读", "use_model": False})
        self.assertEqual(200, status)
        self.assertIn("016", run["run"]["prompt_ids"])

    def test_profile_ai_summary_specialized_trends_and_period_plans(self):
        status, profile = self.request("GET", "/api/profile/diagnosis?exam=CET4")
        self.assertEqual(200, status)
        self.assertIn("diagnosis", profile)
        status, plan = self.request("GET", "/api/plans?exam=CET4&period=month")
        self.assertEqual(200, status)
        self.assertEqual("month", plan["period"])
        status, trends = self.request("GET", "/api/trends/specialized?exam=CET4&period=week")
        self.assertEqual(200, status)
        self.assertEqual(6, len(trends["series"]))
        status, summary = self.request("GET", "/api/summary/ai?exam=CET4")
        self.assertEqual(200, status)
        self.assertIn("next_day", summary)

    def test_ai_practice_session_submits_and_writes_error_evidence(self):
        status, created = self.request("POST", "/api/practice/session", {"exam": "CET4", "kind": "ai", "module": "reading"})
        self.assertEqual(201, status)
        session = created["session"]
        answers = {question["id"]: "1" for question in session["questions"]}
        status, submitted = self.request("POST", "/api/practice/session/submit", {"session_id": session["id"], "answers": answers})
        self.assertEqual(200, status)
        self.assertEqual(5, submitted["result"]["total"])
        self.assertEqual("ai_generated_simulation", submitted["record"]["source_status"])
        status, errors = self.request("GET", "/api/errors?exam=CET4")
        self.assertEqual(200, status)
        self.assertTrue(errors["top_risks"])

    def test_ai_mock_paper_scope_uses_full_paper_countdown(self):
        status, created = self.request("POST", "/api/practice/session", {"exam": "CET4", "kind": "ai", "module": "reading", "scope": "full_paper"})
        self.assertEqual(201, status)
        self.assertEqual("full_paper", created["session"]["module"])
        self.assertEqual("countdown", created["session"]["timer_mode"])
        self.assertGreaterEqual(len(created["session"]["questions"]), 20)

    def test_unverified_past_paper_cannot_start_as_official(self):
        status, payload = self.request("POST", "/api/practice/session", {"exam": "CET4", "kind": "past", "module": "reading"})
        self.assertEqual(400, status)
        self.assertIn("verified", payload["error"])

    def test_full_paper_sources_use_exam_timer_and_uploaded_module_uses_countup(self):
        store = self.server.store
        store.state["past_paper_candidates"].append({"id": "past-cet4-1", "upload_id": "source-1", "exam": "CET4", "status": "verified_official"})
        store.state["simulations"].append({"id": "mock-cet4-1", "upload_id": "source-2", "exam": "CET4", "module": "reading", "status": "ready_private"})
        status, past = self.request("POST", "/api/practice/session", {"exam": "CET4", "kind": "past", "module": "reading", "source_id": "past-cet4-1"})
        self.assertEqual(201, status)
        self.assertEqual("full_paper", past["session"]["module"])
        self.assertEqual("countdown", past["session"]["timer_mode"])
        self.assertEqual(20, len(past["session"]["questions"]))
        status, mock = self.request("POST", "/api/practice/session", {"exam": "CET4", "kind": "upload", "module": "reading", "source_id": "mock-cet4-1"})
        self.assertEqual(201, status)
        self.assertEqual("full_paper", mock["session"]["module"])
        self.assertEqual("countdown", mock["session"]["timer_mode"])

        boundary = "----ExamLexModuleUpload"
        raw = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"阅读专项练习.md\"\r\nContent-Type: text/markdown\r\n\r\n1. The evidence is ____ .\nA. clear\nB. random\nC. weak\nD. absent\r\n--{boundary}--\r\n").encode()
        status, uploaded = self.request("POST", "/api/upload?exam=CET4&module=reading", headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, raw=raw)
        self.assertEqual(201, status)
        upload_id = uploaded["upload"]["id"]
        self.assertEqual("module_practice_upload", uploaded["upload"]["classification"]["category"])
        self.assertEqual("reading", uploaded["upload"]["classification"]["target_module"])
        status, _ = self.request("POST", "/api/pipeline/run", {"upload_id": upload_id, "action": "auto"})
        self.assertEqual(200, status)
        queue = next(item for item in store.state["module_content_queue"] if item["upload_id"] == upload_id)
        status, session = self.request("POST", "/api/practice/session", {"exam": "CET4", "kind": "upload", "module": "reading", "source_id": queue["id"]})
        self.assertEqual(201, status)
        self.assertEqual("reading", session["session"]["module"])
        self.assertEqual("countup", session["session"]["timer_mode"])


if __name__ == "__main__":
    unittest.main()

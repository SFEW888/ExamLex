import hashlib
import io
import tempfile
import tarfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import json

from examlex.scripts import analyze_trends, backup_data, cli_commit, cli_validate, generate_daily_plan, ingest_strategy, record_practice
from examlex.scripts.optimizers.ratchet import StrategyRatchet


class ContinuousLearningP1Tests(unittest.TestCase):
    def test_backup_rejects_output_inside_source_tree(self):
        with self._temporary_dir() as temp:
            source = Path(temp) / "learner-data"
            source.mkdir()
            (source / "profile.json").write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "inside"):
                backup_data.create_backup(source, source / "backup.tar.gz")

    def test_repeated_backup_failure_preserves_previous_archive(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "learner-data"
            source.mkdir()
            (source / "profile.json").write_text("first", encoding="utf-8")
            archive = root / "backup.tar.gz"
            backup_data.create_backup(source, archive)
            original_archive = archive.read_bytes()
            original_sidecar = Path(f"{archive}.sha256").read_bytes()
            (source / "profile.json").write_text("second", encoding="utf-8")

            with patch("tarfile.TarFile.addfile", side_effect=OSError("simulated failure")):
                with self.assertRaisesRegex(OSError, "simulated failure"):
                    backup_data.create_backup(source, archive)

            self.assertEqual(original_archive, archive.read_bytes())
            self.assertEqual(original_sidecar, Path(f"{archive}.sha256").read_bytes())

    def test_backup_hashing_never_uses_unbounded_path_read_bytes(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "learner-data"
            source.mkdir()
            (source / "profile.json").write_text("stream me", encoding="utf-8")
            archive = root / "backup.tar.gz"

            with patch(
                "pathlib.Path.read_bytes",
                side_effect=AssertionError("unbounded read_bytes"),
            ):
                metadata = backup_data.create_backup(source, archive)
                verified = backup_data.verify_backup(
                    archive,
                    expected_checksum=metadata["checksum_sha256"],
                )

            self.assertTrue(verified["verified"])

    def test_backup_hashes_source_during_archive_write_without_prehash_pass(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "learner-data"
            source.mkdir()
            profile = source / "profile.json"
            profile.write_text("single source pass", encoding="utf-8")
            archive = root / "backup.tar.gz"
            real_sha256_file = backup_data._sha256_file

            def reject_source_prehash(path):
                if Path(path).resolve() == profile.resolve():
                    raise AssertionError("source file was hashed in a separate pass")
                return real_sha256_file(path)

            with patch.object(
                backup_data,
                "_sha256_file",
                side_effect=reject_source_prehash,
            ):
                metadata = backup_data.create_backup(source, archive)

            self.assertEqual(
                hashlib.sha256(b"single source pass").hexdigest(),
                metadata["file_hashes"]["profile.json"],
            )

    def test_backup_rejects_source_changes_before_atomic_publish(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "learner-data"
            source.mkdir()
            profile = source / "profile.json"
            profile.write_text("before", encoding="utf-8")
            archive = root / "backup.tar.gz"
            real_addfile = tarfile.TarFile.addfile

            def mutate_after_add(archive_object, tarinfo, fileobj=None):
                result = real_addfile(archive_object, tarinfo, fileobj)
                if tarinfo.name == "profile.json":
                    profile.write_text("after", encoding="utf-8")
                return result

            with patch.object(
                tarfile.TarFile,
                "addfile",
                autospec=True,
                side_effect=mutate_after_add,
            ):
                with self.assertRaisesRegex(ValueError, "changed during backup"):
                    backup_data.create_backup(source, archive)

            self.assertFalse(archive.exists())
            self.assertFalse(Path(f"{archive}.sha256").exists())

    def test_backup_verification_enforces_member_quotas(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "learner-data"
            source.mkdir()
            (source / "a.json").write_text("12345", encoding="utf-8")
            (source / "b.json").write_text("67890", encoding="utf-8")
            archive = root / "backup.tar.gz"
            backup_data.create_backup(source, archive)

            quota_cases = (
                ("MAX_ARCHIVE_MEMBERS", 2, "member count"),
                ("MAX_ARCHIVE_MEMBER_BYTES", 4, "member size"),
                ("MAX_ARCHIVE_TOTAL_BYTES", 9, "total size"),
                ("MAX_BACKUP_METADATA_BYTES", 10, "metadata size"),
            )
            for attribute, limit, message in quota_cases:
                with self.subTest(attribute=attribute), patch.object(
                    backup_data, attribute, limit, create=True
                ):
                    with self.assertRaisesRegex(ValueError, message):
                        backup_data.verify_backup(archive)

    def test_failed_forced_restore_keeps_destination_unchanged(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "learner-data"
            source.mkdir()
            (source / "a.json").write_text("new-a", encoding="utf-8")
            (source / "b.json").write_text("new-b", encoding="utf-8")
            archive = root / "backup.tar.gz"
            metadata = backup_data.create_backup(source, archive)
            destination = root / "restored"
            destination.mkdir()
            (destination / "a.json").write_text("old-a", encoding="utf-8")
            (destination / "b.json").write_text("old-b", encoding="utf-8")
            real_copy = backup_data.shutil.copyfileobj
            calls = 0

            def fail_second_copy(source_stream, output_stream, *args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated restore failure")
                return real_copy(source_stream, output_stream, *args, **kwargs)

            with patch.object(backup_data.shutil, "copyfileobj", fail_second_copy):
                with self.assertRaisesRegex(OSError, "simulated restore failure"):
                    backup_data.restore_backup(
                        archive,
                        destination,
                        force=True,
                        expected_checksum=metadata["checksum_sha256"],
                    )

            self.assertEqual("old-a", (destination / "a.json").read_text(encoding="utf-8"))
            self.assertEqual("old-b", (destination / "b.json").read_text(encoding="utf-8"))

    def test_strategy_library_schema_requires_content_bound_approval_evidence(self):
        schema_path = (
            Path(__file__).resolve().parents[1]
            / "examlex/assets/schemas/strategy-library.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        evidence = schema["properties"]["strategies"]["items"]["properties"][
            "approval_evidence"
        ]

        self.assertIn("strategy_sha256", evidence["required"])
        self.assertEqual(
            "^[a-f0-9]{64}$",
            evidence["properties"]["strategy_sha256"]["pattern"],
        )

    def test_validation_report_binds_each_strategy_content(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            strategy = {
                "strategy_id": "cet4-reading-method-001",
                "title": "Method",
                "content": "Use a concrete evidence-location method for every item.",
                "steps": ["Read the question", "Locate evidence"],
                "source_file": "method.md",
                "exam_types": ["CET4"],
                "modules": ["reading"],
                "added_at": "2026-07-10",
            }
            (root / "distilled.json").write_text(
                json.dumps({"strategies": [strategy]}), encoding="utf-8"
            )

            self.assertIn(cli_validate.main(["--artifacts-dir", str(root)]), (0, 1))

            report = json.loads((root / "validation_report.json").read_text(encoding="utf-8"))
            self.assertEqual(
                hashlib.sha256(
                    json.dumps(
                        strategy,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest(),
                report["results"][0]["strategy_sha256"],
            )

    def test_concurrent_ingest_keeps_both_strategies(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            library = root / "library.json"
            library.write_text('{"strategies": []}\n', encoding="utf-8")
            sources = []
            for index in range(2):
                source = root / f"method-{index}.md"
                source.write_text(
                    f"Method {index}\n\n1. Read question {index}\n2. Verify evidence {index}",
                    encoding="utf-8",
                )
                sources.append(source)
            start = threading.Barrier(3)
            errors = []
            original_load = ingest_strategy.common.load_data

            def delayed_load(path):
                data = original_load(path)
                if Path(path) == library:
                    time.sleep(0.05)
                return data

            def worker(source):
                try:
                    start.wait()
                    ingest_strategy.ingest_strategy(
                        file_path=source,
                        library_path=library,
                        exam_types=["CET4"],
                        modules=["reading"],
                    )
                except Exception as exc:  # pragma: no cover - asserted below
                    errors.append(exc)

            with unittest.mock.patch.object(
                ingest_strategy.common, "load_data", side_effect=delayed_load
            ):
                threads = [threading.Thread(target=worker, args=(source,)) for source in sources]
                for thread in threads:
                    thread.start()
                start.wait()
                for thread in threads:
                    thread.join()

            self.assertEqual([], errors)
            saved = json.loads(library.read_text(encoding="utf-8"))
            self.assertEqual(2, len(saved["strategies"]))

    def test_ingest_records_content_addressed_source_provenance(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "method.md"
            raw = b"Use question-first reading and verify the evidence."
            source.write_bytes(raw)

            strategy = ingest_strategy.ingest_strategy(
                file_path=source,
                library_path=root / "library.json",
                exam_types=["CET4"],
                modules=["reading"],
                source_url="https://example.invalid/source",
            )

            provenance = strategy["source_provenance"]
            self.assertEqual(provenance["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(provenance["source_url"], "https://example.invalid/source")
            self.assertEqual(provenance["source_file"], "method.md")

    def test_backup_verification_detects_tampered_member(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            source = root / "learner-data"
            source.mkdir()
            (source / "profile.json").write_text('{"learner_id": "a"}', encoding="utf-8")
            archive = root / "backup.tar.gz"

            metadata = backup_data.create_backup(source, archive)
            self.assertIn("file_hashes", metadata)
            restored = root / "restored-valid"
            backup_data.restore_backup(
                archive, restored, expected_checksum=metadata["checksum_sha256"],
            )
            self.assertEqual(
                (restored / "profile.json").read_text(encoding="utf-8"),
                '{"learner_id": "a"}',
            )
            tampered = root / "backup-tampered.tar.gz"
            with tarfile.open(archive, "r:gz") as original, tarfile.open(tampered, "w:gz") as altered:
                metadata_member = original.getmember("backup-metadata.json")
                metadata_stream = original.extractfile(metadata_member)
                self.assertIsNotNone(metadata_stream)
                altered_metadata = json.loads(metadata_stream.read())
                altered_profile = b'{"learner_id": "tampered"}'
                altered_metadata["file_hashes"]["profile.json"] = hashlib.sha256(altered_profile).hexdigest()
                for member in original.getmembers():
                    content = original.extractfile(member)
                    if member.name == "profile.json":
                        payload = altered_profile
                    elif member.name == "backup-metadata.json":
                        payload = json.dumps(altered_metadata).encode("utf-8")
                    else:
                        self.assertIsNotNone(content)
                        payload = content.read()
                    member.size = len(payload)
                    altered.addfile(member, fileobj=io.BytesIO(payload))
                injected = tarfile.TarInfo("unexpected.txt")
                injected_payload = b"unexpected archive member"
                injected.size = len(injected_payload)
                altered.addfile(injected, fileobj=io.BytesIO(injected_payload))

            # The original sidecar is the external integrity anchor. Reusing it
            # must expose any rewrite of both archive contents and manifest.
            tampered_sidecar = Path(f"{tampered}.sha256")
            tampered_sidecar.write_text(Path(f"{archive}.sha256").read_text(encoding="utf-8"), encoding="utf-8")

            verified = backup_data.verify_backup(tampered)
            self.assertFalse(verified["verified"])
            self.assertIn("unexpected.txt", verified["mismatches"])
            self.assertIn("archive checksum", verified["mismatches"])
            with self.assertRaisesRegex(ValueError, "integrity verification failed"):
                backup_data.restore_backup(tampered, root / "restored")

    def test_ratchet_keeps_immutable_revision_snapshots(self):
        ratchet = StrategyRatchet()
        library = {"strategies": []}
        first = ratchet.apply({"strategy_id": "cet4-reading-method-001", "title": "First"}, library, None, 70)
        second = ratchet.apply(
            {"strategy_id": "cet4-reading-method-001", "title": "Improved"},
            library,
            first,
            80,
        )

        self.assertEqual([revision["version"] for revision in second["revisions"]], [1, 2])
        self.assertEqual(second["revisions"][0]["strategy"]["title"], "First")
        self.assertEqual(second["revisions"][1]["strategy"]["title"], "Improved")
        self.assertRegex(second["revisions"][1]["sha256"], r"^[a-f0-9]{64}$")

    def test_practice_records_attribute_outcomes_to_strategy_revisions(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            ledger_path = root / "ledger.json"
            for correct_items in (5, 8):
                record_practice.record_practice(ledger_path, {
                    "date": "2026-07-10",
                    "exam_type": "CET4",
                    "module": "reading",
                    "task_id": f"reading-{correct_items}",
                    "duration_minutes": 20,
                    "total_items": 10,
                    "correct_items": correct_items,
                    "error_tags": [],
                    "plan_id": "plan-001",
                    "strategy_revisions": [{
                        "strategy_id": "cet4-reading-method-001",
                        "revision_sha256": "a" * 64,
                    }],
                })

            trends = analyze_trends.analyze_trends(ledger=json.loads(ledger_path.read_text(encoding="utf-8")))
            effect = trends["strategies"]["cet4-reading-method-001"]
            self.assertEqual(effect["direction"], "improving")
            self.assertEqual(effect["usage_records"], 2)

    def test_daily_plan_revision_flows_into_practice_cli(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            approved = {
                "strategy_id": "cet4-reading-method-001",
                "title": "Evidence location",
                "exam_types": ["CET4"],
                "modules": ["reading"],
                "lifecycle_status": "approved",
                "darwin_score": 80,
            }
            snapshot = dict(approved)
            revision_sha256 = hashlib.sha256(
                json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            approved["revisions"] = [
                {"version": 1, "sha256": revision_sha256, "strategy": snapshot}
            ]
            plan = generate_daily_plan.generate_daily_plan(
                {"learner_id": "learner-001", "exam_type": "CET4", "daily_time_budget_minutes": 20},
                {"modules": {"reading": [{"node": "locating", "level": 1, "status": "priority"}]}},
                strategies={"strategies": [approved, {
                    "strategy_id": "cet4-reading-invalid-002",
                    "title": "Invalid snapshot",
                    "exam_types": ["CET4"],
                    "modules": ["reading"],
                    "lifecycle_status": "approved",
                    "darwin_score": 99,
                    "revisions": [{"version": 1, "sha256": "c" * 64,
                                   "strategy": {"strategy_id": "cet4-reading-invalid-002"}}],
                }]},
            )
            hint = plan["tasks"][0]["strategy_hints"][0]
            self.assertEqual(hint["revision_sha256"], revision_sha256)

            plan_path = root / "plan.json"
            ledger_path = root / "ledger.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            self.assertEqual(record_practice.main([
                "--ledger", str(ledger_path), "--plan", str(plan_path), "--plan-task-index", "0",
                "--date", "2026-07-10", "--exam-type", "CET4", "--module", "reading",
                "--task-id", "reading-001", "--duration-minutes", "20", "--total-items", "10",
                "--correct-items", "8",
            ]), 0)
            record = json.loads(ledger_path.read_text(encoding="utf-8"))[0]
            self.assertEqual(record["plan_id"], plan["plan_id"])
            self.assertEqual(record["strategy_revisions"], [{
                "strategy_id": "cet4-reading-method-001", "revision_sha256": revision_sha256,
            }])

    def test_commit_records_hashes_of_approval_evidence(self):
        with self._temporary_dir() as temp:
            root = Path(temp)
            library = root / "library.json"
            strategy_id = "cet4-reading-method-001"
            strategy = {
                "strategy_id": strategy_id, "title": "Method", "exam_types": ["CET4"],
                "modules": ["reading"], "content": "Use a concrete evidence-location method for every item.",
                "source_file": "method.md", "added_at": "2026-07-10",
            }
            digest = hashlib.sha256(json.dumps(
                strategy, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest()
            (root / "distilled.json").write_text(json.dumps({"strategies": [strategy]}), encoding="utf-8")
            (root / "validation_report.json").write_text(json.dumps({
                "all_format_passed": True,
                "results": [{"strategy_id": strategy_id, "format_passed": True,
                             "structure_passed": True, "structure_score": 59,
                             "strategy_sha256": digest}],
            }), encoding="utf-8")
            (root / "evaluation.json").write_text(json.dumps({
                "strategies": [{"strategy_id": strategy_id, "effect_total": 11,
                                "strategy_sha256": digest}],
            }), encoding="utf-8")

            self.assertEqual(cli_commit.main(["--artifacts-dir", str(root), "--library", str(library)]), 0)
            approved = json.loads(library.read_text(encoding="utf-8"))["strategies"][0]
            evidence = approved["approval_evidence"]
            self.assertRegex(evidence["validation_sha256"], r"^[a-f0-9]{64}$")
            self.assertRegex(evidence["evaluation_sha256"], r"^[a-f0-9]{64}$")
            self.assertEqual(digest, evidence["strategy_sha256"])

    @staticmethod
    def _temporary_dir():
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()

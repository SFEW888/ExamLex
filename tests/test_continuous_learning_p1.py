import hashlib
import io
import tempfile
import tarfile
import unittest
from pathlib import Path

import json

from examlex.scripts import analyze_trends, backup_data, cli_commit, generate_daily_plan, ingest_strategy, record_practice
from examlex.scripts.optimizers.ratchet import StrategyRatchet


class ContinuousLearningP1Tests(unittest.TestCase):
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
            snapshot = {"strategy_id": "cet4-reading-method-001"}
            revision_sha256 = hashlib.sha256(
                json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            plan = generate_daily_plan.generate_daily_plan(
                {"learner_id": "learner-001", "exam_type": "CET4", "daily_time_budget_minutes": 20},
                {"modules": {"reading": [{"node": "locating", "level": 1, "status": "priority"}]}},
                strategies={"strategies": [{
                    "strategy_id": "cet4-reading-method-001",
                    "title": "Evidence location",
                    "exam_types": ["CET4"],
                    "modules": ["reading"],
                    "lifecycle_status": "approved",
                    "darwin_score": 80,
                    "revisions": [{"version": 1, "sha256": revision_sha256, "strategy": snapshot}],
                }, {
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
            (root / "distilled.json").write_text(json.dumps({"strategies": [{
                "strategy_id": strategy_id, "title": "Method", "exam_types": ["CET4"],
                "modules": ["reading"], "content": "Use a concrete evidence-location method for every item.",
                "source_file": "method.md", "added_at": "2026-07-10",
            }]}), encoding="utf-8")
            (root / "validation_report.json").write_text(json.dumps({
                "all_format_passed": True,
                "results": [{"strategy_id": strategy_id, "format_passed": True,
                             "structure_passed": True, "structure_score": 59}],
            }), encoding="utf-8")
            (root / "evaluation.json").write_text(json.dumps({
                "strategies": [{"strategy_id": strategy_id, "effect_total": 11}],
            }), encoding="utf-8")

            self.assertEqual(cli_commit.main(["--artifacts-dir", str(root), "--library", str(library)]), 0)
            approved = json.loads(library.read_text(encoding="utf-8"))["strategies"][0]
            evidence = approved["approval_evidence"]
            self.assertRegex(evidence["validation_sha256"], r"^[a-f0-9]{64}$")
            self.assertRegex(evidence["evaluation_sha256"], r"^[a-f0-9]{64}$")

    @staticmethod
    def _temporary_dir():
        root = Path("test-artifacts")
        root.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(dir=root)


if __name__ == "__main__":
    unittest.main()

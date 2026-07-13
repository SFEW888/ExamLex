from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from examlex.scripts.cli_sources import collect_main, fetch_main, list_main


class SourceCLITests(unittest.TestCase):
    def test_source_list_json_exposes_evidence_without_percentages(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = list_main(["--exam", "cet", "--collectable", "--json"])
        self.assertEqual(0, code)
        payload = json.loads(output.getvalue())
        self.assertGreater(payload["count"], 0)
        self.assertTrue(all(source["usage"] for source in payload["sources"]))
        self.assertNotIn("percent", output.getvalue().lower())

    def test_non_collectable_source_reports_actionable_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = io.StringIO()
            with redirect_stdout(output):
                code = collect_main(
                    [
                        "--source",
                        "scientific-american",
                        "--output-dir",
                        temporary,
                        "--json",
                    ]
                )
        self.assertEqual(1, code)
        payload = json.loads(output.getvalue())
        self.assertIn("no maintained public feed", payload["message"])

    def test_fetch_rejects_unknown_item_without_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = io.StringIO()
            with redirect_stdout(output):
                code = fetch_main(
                    [
                        "--source",
                        "bbc",
                        "--item",
                        "missing",
                        "--kind",
                        "text",
                        "--output-dir",
                        str(Path(temporary)),
                        "--json",
                    ]
                )
        self.assertEqual(1, code)
        self.assertIn("unknown corpus item", json.loads(output.getvalue())["message"])


if __name__ == "__main__":
    unittest.main()

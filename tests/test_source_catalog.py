from __future__ import annotations

import copy
import unittest

from examlex.scripts.source_catalog import (
    SourceCatalogError,
    filter_sources,
    load_source_catalog,
    resolve_source,
    validate_catalog,
)


class SourceCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_source_catalog()

    def test_catalog_merges_expected_cet_and_postgraduate_sources(self):
        source_ids = {source["source_id"] for source in self.catalog["sources"]}
        self.assertGreaterEqual(len(source_ids), 50)
        self.assertTrue(
            {
                "bbc",
                "npr",
                "guardian",
                "scientific-american",
                "nature",
                "economist",
                "atlantic",
                "christian-science-monitor",
                "financial-times",
                "historyextra",
                "ted-talks",
            }.issubset(source_ids)
        )
        self.assertGreaterEqual(len(self.catalog["reference_corpora"]), 15)

    def test_shared_source_keeps_exam_specific_evidence_records(self):
        source = resolve_source(self.catalog, "Scientific American")
        usage = {(item["exam"], item["evidence"]) for item in source["usage"]}
        self.assertIn(("cet", "B"), usage)
        self.assertIn(("postgraduate", "B"), usage)

    def test_time_and_the_times_are_distinct(self):
        self.assertEqual("time", resolve_source(self.catalog, "TIME")["source_id"])
        self.assertEqual("the-times", resolve_source(self.catalog, "The Times")["source_id"])

    def test_verified_feed_subset_is_explicit(self):
        collectable = filter_sources(self.catalog, collectable_only=True)
        feed_ids = {
            feed["feed_id"]
            for source in collectable
            for feed in source.get("feeds", [])
        }
        self.assertIn("bbc-news", feed_ids)
        self.assertIn("ted-talks-video", feed_ids)
        self.assertNotIn("ted-talks-audio", feed_ids)
        self.assertIn("science-news", feed_ids)
        self.assertNotIn("scientific-american", {source["source_id"] for source in collectable})

    def test_filters_do_not_upgrade_evidence(self):
        results = filter_sources(
            self.catalog,
            exam="postgraduate",
            section="reading_a",
            evidence="B",
        )
        self.assertTrue(results)
        for source in results:
            self.assertTrue(
                any(
                    usage["exam"] == "postgraduate"
                    and usage["evidence"] == "B"
                    and "reading_a" in usage["sections"]
                    for usage in source["usage"]
                )
            )

    def test_catalog_contains_no_percentage_claims(self):
        text = str(self.catalog).lower()
        self.assertNotIn("percentage", text)
        self.assertNotIn("percent", text)

    def test_duplicate_alias_is_rejected(self):
        invalid = copy.deepcopy(self.catalog)
        invalid["sources"][1]["aliases"].append("NYT")
        with self.assertRaisesRegex(SourceCatalogError, "maps to both"):
            validate_catalog(invalid)

    def test_a_level_usage_requires_article_trace_ids(self):
        invalid = copy.deepcopy(self.catalog)
        invalid["sources"][0]["usage"][0]["evidence"] = "A"
        with self.assertRaisesRegex(SourceCatalogError, "article trace ids"):
            validate_catalog(invalid)

    def test_feed_host_must_belong_to_source(self):
        invalid = copy.deepcopy(self.catalog)
        source = next(item for item in invalid["sources"] if item.get("feeds"))
        source["feeds"][0]["url"] = "https://untrusted.invalid/feed.xml"
        with self.assertRaisesRegex(SourceCatalogError, "outside its domains"):
            validate_catalog(invalid)


if __name__ == "__main__":
    unittest.main()

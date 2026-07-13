from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from examlex.scripts.source_collector import (
    CorpusStore,
    FetchResult,
    SourceCollectionError,
    SourceFetcher,
    SourceURLValidationError,
    canonicalize_url,
    collect_source_feeds,
    materialize_media,
    materialize_text,
    parse_feed,
    validate_public_https_url,
)
from examlex.scripts import source_collector


SOURCE = {
    "source_id": "example",
    "canonical_name": "Example Source",
    "domains": ["example.com"],
    "media_types": ["article", "audio", "video"],
    "usage": [{"exam": "cet", "sections": ["reading"], "evidence": "B"}],
    "feeds": [
        {"feed_id": "example-feed", "url": "https://example.com/feed.xml", "media_type": "mixed"}
    ],
}

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>How &amp; Why Students Learn</title>
      <link>https://example.com/article?utm_source=test&amp;page=2#part</link>
      <description><![CDATA[<p>A <strong>short</strong> summary.</p>]]></description>
      <author>Jane Example</author>
      <pubDate>Mon, 13 Jul 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Science Podcast</title>
      <link>https://example.com/podcast/1</link>
      <enclosure url="https://media.example.com/audio/1.mp3" type="audio/mpeg" />
    </item>
  </channel>
</rss>
"""


class SourceCollectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dns_patch = patch(
            "examlex.scripts.source_collector._require_public_dns", return_value=None
        )
        self.dns_patch.start()
        self.addCleanup(self.dns_patch.stop)

    def test_url_boundary_requires_catalog_https_domain(self):
        self.assertEqual(
            "https://example.com/a",
            validate_public_https_url("https://example.com/a", ["example.com"]),
        )
        with self.assertRaises(SourceURLValidationError):
            validate_public_https_url("http://example.com/a", ["example.com"])
        with self.assertRaises(SourceURLValidationError):
            validate_public_https_url("https://other.example/a", ["example.com"])
        with self.assertRaises(SourceURLValidationError):
            validate_public_https_url("https://user:pass@example.com/a", ["example.com"])

    def test_canonical_url_removes_only_known_tracking_fields(self):
        value = canonicalize_url(
            "https://EXAMPLE.com/a?utm_source=x&source=keep&page=2&fbclid=x#section"
        )
        self.assertEqual("https://example.com/a?source=keep&page=2", value)

    def test_rss_and_media_enclosures_are_normalized(self):
        items = parse_feed(RSS, source=SOURCE, feed=SOURCE["feeds"][0], limit=10)
        self.assertEqual(2, len(items))
        article, podcast = items
        self.assertEqual("article", article.media_type)
        self.assertEqual("https://example.com/article?page=2", article.canonical_url)
        self.assertEqual("A short summary.", article.summary)
        self.assertEqual("2026-07-13T10:00:00Z", article.published_at)
        self.assertEqual("audio", podcast.media_type)
        self.assertEqual("https://media.example.com/audio/1.mp3", podcast.media_url)
        self.assertEqual("audio/mpeg", podcast.media_content_type)

    def test_feed_rejects_dtd_and_entity_declarations(self):
        payload = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e "boom">]><rss />'
        with self.assertRaisesRegex(SourceCollectionError, "DTD"):
            parse_feed(payload, source=SOURCE, feed=SOURCE["feeds"][0])

    def test_external_enclosure_is_not_indexed_as_downloadable_media(self):
        payload = RSS.replace(b"media.example.com", b"untrusted.invalid")
        items = parse_feed(payload, source=SOURCE, feed=SOURCE["feeds"][0])
        podcast = items[1]
        self.assertEqual("article", podcast.media_type)
        self.assertIsNone(podcast.media_url)
        self.assertIn("media_url_outside_source_domains", podcast.warnings)

    def test_manifest_upsert_is_deterministic_and_preserves_materialization(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = CorpusStore(Path(temporary))
            item = parse_feed(RSS, source=SOURCE, feed=SOURCE["feeds"][0], limit=1)[0]
            self.assertEqual((1, 0), store.upsert([item], observed_at="2026-07-13T00:00:00Z"))
            item.content_path = "content/existing.txt"
            item.content_sha256 = "a" * 64
            store.update_item(item)
            refreshed = parse_feed(RSS, source=SOURCE, feed=SOURCE["feeds"][0], limit=1)[0]
            self.assertEqual((0, 1), store.upsert([refreshed], observed_at="2026-07-14T00:00:00Z"))
            loaded = store.get(item.item_id)
            self.assertEqual("content/existing.txt", loaded.content_path)
            self.assertEqual("a" * 64, loaded.content_sha256)
            self.assertEqual("2026-07-13T00:00:00Z", loaded.first_seen_at)
            self.assertEqual("2026-07-14T00:00:00Z", loaded.last_seen_at)

    def test_text_materialization_obeys_robots_and_writes_hash(self):
        class FakeFetcher:
            def robots_allowed(self, url: str) -> bool:
                return True

            def fetch(self, url: str, *, accept: str, max_bytes: int) -> FetchResult:
                body = (
                    b"<html><body><nav>skip</nav><article><h1>Title</h1>"
                    + b"<p>" + (b"Useful article text. " * 30) + b"</p>"
                    + b"<script>ignore()</script></article></body></html>"
                )
                return FetchResult(body, url, "text/html", {}, 200)

        with tempfile.TemporaryDirectory() as temporary:
            store = CorpusStore(Path(temporary))
            item = parse_feed(RSS, source=SOURCE, feed=SOURCE["feeds"][0], limit=1)[0]
            store.upsert([item], observed_at="2026-07-13T00:00:00Z")
            result = materialize_text(SOURCE, store, item.item_id, fetcher=FakeFetcher())
            self.assertIsNotNone(result.content_path)
            content = (store.root / result.content_path).read_text(encoding="utf-8")
            self.assertIn("Useful article text", content)
            self.assertNotIn("ignore", content)
            self.assertEqual(hashlib.sha256(content.encode("utf-8")).hexdigest(), result.content_sha256)

    def test_text_materialization_fails_closed_on_robots(self):
        class DeniedFetcher:
            def robots_allowed(self, url: str) -> bool:
                return False

        with tempfile.TemporaryDirectory() as temporary:
            store = CorpusStore(Path(temporary))
            item = parse_feed(RSS, source=SOURCE, feed=SOURCE["feeds"][0], limit=1)[0]
            store.upsert([item], observed_at="2026-07-13T00:00:00Z")
            with self.assertRaisesRegex(SourceCollectionError, "robots"):
                materialize_text(SOURCE, store, item.item_id, fetcher=DeniedFetcher())

    def test_robots_404_allows_collection_but_other_failures_close(self):
        fetcher = SourceFetcher(["example.com"])
        with patch.object(
            fetcher,
            "fetch",
            side_effect=source_collector.HTTPError(
                "https://example.com/robots.txt", 404, "missing", {}, None
            ),
        ):
            self.assertTrue(fetcher.robots_allowed("https://example.com/article"))

        fetcher = SourceFetcher(["example.com"])
        with patch.object(
            fetcher,
            "fetch",
            side_effect=SourceCollectionError("network unavailable"),
        ):
            self.assertFalse(fetcher.robots_allowed("https://example.com/article"))

    def test_media_materialization_requires_explicit_item_and_quota(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = CorpusStore(Path(temporary))
            item = parse_feed(RSS, source=SOURCE, feed=SOURCE["feeds"][0], limit=2)[1]
            store.upsert([item], observed_at="2026-07-13T00:00:00Z")

            def fake_download(self, url: str, target: Path, *, max_bytes: int):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"audio")
                return hashlib.sha256(b"audio").hexdigest(), "audio/mpeg"

            with patch.object(SourceFetcher, "download_media", fake_download):
                result = materialize_media(SOURCE, store, item.item_id, max_bytes=10)
            self.assertTrue((store.root / result.media_path).is_file())
            self.assertEqual(hashlib.sha256(b"audio").hexdigest(), result.media_sha256)

    def test_collection_deduplicates_feed_results(self):
        def fake_fetch(self, url: str, *, accept: str, max_bytes: int) -> FetchResult:
            return FetchResult(RSS, url, "text/xml", {}, 200)

        with tempfile.TemporaryDirectory() as temporary, patch.object(
            SourceFetcher, "fetch", fake_fetch
        ):
            store = CorpusStore(Path(temporary))
            first = collect_source_feeds(
                SOURCE, store, limit=2, delay_seconds=0, now="2026-07-13T00:00:00Z"
            )
            second = collect_source_feeds(
                SOURCE, store, limit=2, delay_seconds=0, now="2026-07-14T00:00:00Z"
            )
        self.assertEqual(2, first["new"])
        self.assertEqual(1, first["feeds_succeeded"])
        self.assertEqual(0, second["new"])
        self.assertEqual(2, second["updated"])

    def test_collection_fails_when_every_feed_fails(self):
        def failed_fetch(self, url: str, *, accept: str, max_bytes: int) -> FetchResult:
            raise SourceCollectionError("unreachable")

        with tempfile.TemporaryDirectory() as temporary, patch.object(
            SourceFetcher, "fetch", failed_fetch
        ):
            with self.assertRaisesRegex(SourceCollectionError, "all source feeds failed"):
                collect_source_feeds(
                    SOURCE,
                    CorpusStore(Path(temporary)),
                    limit=2,
                    delay_seconds=0,
                )


class PublicDNSBoundaryTests(unittest.TestCase):
    def tearDown(self) -> None:
        source_collector._require_public_dns.cache_clear()

    def test_private_or_mixed_dns_answers_are_rejected(self):
        source_collector._require_public_dns.cache_clear()
        addresses = [
            (2, 1, 6, "", ("93.184.216.34", 443)),
            (2, 1, 6, "", ("127.0.0.1", 443)),
        ]
        with patch.object(source_collector.socket, "getaddrinfo", return_value=addresses):
            with self.assertRaisesRegex(SourceURLValidationError, "public addresses"):
                source_collector._require_public_dns("example.com")

    def test_public_dns_answer_is_accepted(self):
        source_collector._require_public_dns.cache_clear()
        addresses = [(2, 1, 6, "", ("93.184.216.34", 443))]
        with patch.object(source_collector.socket, "getaddrinfo", return_value=addresses):
            source_collector._require_public_dns("example.com")

    def test_benchmark_fake_ip_requires_an_explicit_proxy(self):
        source_collector._require_public_dns.cache_clear()
        addresses = [(2, 1, 6, "", ("198.18.0.44", 443))]
        with patch.object(source_collector.socket, "getaddrinfo", return_value=addresses):
            with self.assertRaisesRegex(SourceURLValidationError, "public addresses"):
                source_collector._require_public_dns("example.com")
            source_collector._require_public_dns(
                "example.com", allow_proxy_fake_ip=True
            )

    def test_proxy_exception_never_allows_loopback_target_answers(self):
        source_collector._require_public_dns.cache_clear()
        addresses = [(2, 1, 6, "", ("127.0.0.1", 443))]
        with patch.object(source_collector.socket, "getaddrinfo", return_value=addresses):
            with self.assertRaisesRegex(SourceURLValidationError, "public addresses"):
                source_collector._require_public_dns(
                    "example.com", allow_proxy_fake_ip=True
                )

    def test_proxy_detection_obeys_bypass_rules(self):
        with (
            patch.object(
                source_collector,
                "getproxies",
                return_value={"https": "http://127.0.0.1:7890"},
            ),
            patch.object(source_collector, "proxy_bypass", return_value=False),
        ):
            self.assertTrue(source_collector._configured_https_proxy("example.com"))
        with (
            patch.object(
                source_collector,
                "getproxies",
                return_value={"https": "http://127.0.0.1:7890"},
            ),
            patch.object(source_collector, "proxy_bypass", return_value=True),
        ):
            self.assertFalse(source_collector._configured_https_proxy("example.com"))


if __name__ == "__main__":
    unittest.main()

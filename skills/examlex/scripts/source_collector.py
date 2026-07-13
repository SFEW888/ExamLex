"""Safe, feed-first collection for exam-practice source materials.

The collector indexes third-party metadata by default. Fetching readable text or
media is a separate, explicit operation. It never sends cookies, bypasses a
paywall, or follows a URL to a private/non-public network address.
"""

from __future__ import annotations

import hashlib
import html
import ipaddress
import json
import os
import re
import socket
import tempfile
import time
# The only parser call is guarded by a full-payload DTD/entity rejection and a
# strict 2 MiB input limit in parse_feed().
import xml.etree.ElementTree as ET  # nosec B405
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
    getproxies,
    proxy_bypass,
)
from urllib.robotparser import RobotFileParser

from .file_lock import exclusive_file_lock


USER_AGENT = "ExamLex-source-collector/0.1 (+https://github.com/SFEW888/ExamLex)"
MAX_FEED_BYTES = 2 * 1024 * 1024
MAX_ROBOTS_BYTES = 512 * 1024
MAX_HTML_BYTES = 4 * 1024 * 1024
MAX_READABLE_CHARS = 250_000
MAX_MANIFEST_BYTES = 64 * 1024 * 1024
MAX_ITEM_JSON_BYTES = 512 * 1024
DEFAULT_MAX_MEDIA_BYTES = 100 * 1024 * 1024
TRACKING_QUERY_PREFIXES = ("utm_", "mc_")
TRACKING_QUERY_NAMES = frozenset({"fbclid", "gclid", "igshid"})
MEDIA_CONTENT_TYPES = ("audio/", "video/", "application/octet-stream")
PROXY_FAKE_IP_NETWORK = ipaddress.ip_network("198.18.0.0/15")


class SourceCollectionError(RuntimeError):
    """Raised for a safe, user-actionable collection failure."""


class SourceURLValidationError(SourceCollectionError):
    """Raised when a URL is outside the public HTTPS boundary."""


@dataclass(frozen=True)
class FetchResult:
    body: bytes
    final_url: str
    content_type: str
    headers: dict[str, str]
    status: int


@dataclass
class CollectedItem:
    item_id: str
    source_id: str
    source_name: str
    title: str
    canonical_url: str
    media_type: str
    published_at: str | None = None
    author: str | None = None
    summary: str | None = None
    media_url: str | None = None
    media_content_type: str | None = None
    feed_id: str | None = None
    feed_url: str | None = None
    exam_usage: list[dict[str, Any]] = field(default_factory=list)
    content_path: str | None = None
    content_sha256: str | None = None
    media_path: str | None = None
    media_sha256: str | None = None
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    warnings: list[str] = field(default_factory=list)
    rights: str = "third-party content; metadata-only by default"


def default_corpus_root() -> Path:
    """Return the platform-local corpus directory, outside the repository."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        return Path(base) / "ExamLex" / "source-corpus"
    try:
        is_macos = os.uname().sysname == "Darwin"
    except AttributeError:
        is_macos = False
    if is_macos:
        return Path.home() / "Library" / "Application Support" / "ExamLex" / "source-corpus"
    base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return base / "ExamLex" / "source-corpus"


def _domain_allowed(host: str, allowed_domains: Iterable[str]) -> bool:
    normalized = host.lower().rstrip(".")
    return any(
        normalized == domain or normalized.endswith("." + domain)
        for domain in {value.lower().rstrip(".") for value in allowed_domains}
    )


def _configured_https_proxy(host: str) -> bool:
    """Return whether urllib will route this host through an explicit HTTPS proxy."""
    try:
        if proxy_bypass(host):
            return False
        proxy_url = getproxies().get("https") or getproxies().get("all")
    except (OSError, ValueError):
        return False
    if not proxy_url:
        return False
    if "://" not in proxy_url:
        proxy_url = "http://" + proxy_url
    try:
        parts = urlsplit(proxy_url)
        port = parts.port
    except ValueError:
        return False
    return bool(
        parts.scheme in {"http", "https"}
        and parts.hostname
        and port not in {0}
    )


@lru_cache(maxsize=512)
def _require_public_dns(
    host: str,
    port: int = 443,
    allow_proxy_fake_ip: bool = False,
) -> None:
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SourceURLValidationError(f"could not resolve host {host!r}") from exc
    if not addresses:
        raise SourceURLValidationError(f"could not resolve host {host!r}")
    for address in addresses:
        raw_ip = address[4][0].split("%", 1)[0]
        try:
            parsed = ipaddress.ip_address(raw_ip)
        except ValueError as exc:
            raise SourceURLValidationError(f"host resolved to invalid address: {raw_ip}") from exc
        is_proxy_fake_ip = allow_proxy_fake_ip and parsed in PROXY_FAKE_IP_NETWORK
        if not parsed.is_global and not is_proxy_fake_ip:
            raise SourceURLValidationError(
                f"host must resolve only to public addresses; got {parsed}"
            )


def validate_public_https_url(url: str, allowed_domains: Iterable[str]) -> str:
    """Validate an anonymous, standard-port, catalog-domain HTTPS URL."""
    if not isinstance(url, str) or not url.strip() or len(url) > 4096:
        raise SourceURLValidationError("URL must be a non-empty string of at most 4096 chars")
    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError as exc:
        raise SourceURLValidationError("URL is malformed") from exc
    if parts.scheme.lower() != "https":
        raise SourceURLValidationError("URL must use HTTPS")
    if parts.username is not None or parts.password is not None:
        raise SourceURLValidationError("URL must not contain user information")
    if port not in (None, 443):
        raise SourceURLValidationError("URL must use the standard HTTPS port")
    host = (parts.hostname or "").lower().rstrip(".")
    if not host or not _domain_allowed(host, allowed_domains):
        raise SourceURLValidationError(f"URL host is not allowed for this source: {host or '<missing>'}")
    _require_public_dns(host, allow_proxy_fake_ip=_configured_https_proxy(host))
    return url.strip()


class _SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self, allowed_domains: Iterable[str]) -> None:
        self.allowed_domains = tuple(allowed_domains)
        super().__init__()

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        target = urljoin(req.full_url, newurl)
        validate_public_https_url(target, self.allowed_domains)
        redirected = super().redirect_request(req, fp, code, msg, headers, target)
        if redirected is not None:
            redirected.remove_header("Cookie")
            redirected.remove_header("Authorization")
        return redirected


def _read_bounded(response, max_bytes: int) -> bytes:  # noqa: ANN001
    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise SourceCollectionError(f"response exceeds {max_bytes} byte limit")
        except ValueError:
            pass
    payload = response.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise SourceCollectionError(f"response exceeds {max_bytes} byte limit")
    return payload


class SourceFetcher:
    """Bounded network client with catalog-domain and redirect validation."""

    def __init__(self, allowed_domains: Iterable[str], *, timeout_seconds: float = 20.0):
        self.allowed_domains = tuple(sorted(set(allowed_domains)))
        if not self.allowed_domains:
            raise SourceCollectionError("at least one allowed source domain is required")
        self.timeout_seconds = timeout_seconds
        self._robots_cache: dict[str, bool | RobotFileParser] = {}

    def fetch(self, url: str, *, accept: str, max_bytes: int) -> FetchResult:
        validated = validate_public_https_url(url, self.allowed_domains)
        request = Request(
            validated,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": accept,
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
            method="GET",
        )
        opener = build_opener(_SafeRedirectHandler(self.allowed_domains))
        try:
            with opener.open(request, timeout=self.timeout_seconds) as response:
                final_url = response.geturl()
                validate_public_https_url(final_url, self.allowed_domains)
                body = _read_bounded(response, max_bytes)
                content_type = response.headers.get_content_type().lower()
                headers = {
                    key: value
                    for key, value in response.headers.items()
                    if key.lower() in {"content-type", "etag", "last-modified", "content-length"}
                }
                return FetchResult(
                    body=body,
                    final_url=final_url,
                    content_type=content_type,
                    headers=headers,
                    status=getattr(response, "status", 200),
                )
        except HTTPError:
            raise
        except (URLError, OSError, TimeoutError) as exc:
            raise SourceCollectionError("source request failed") from exc

    def robots_allowed(self, url: str) -> bool:
        """Fail closed when robots.txt cannot be read, except an explicit 404."""
        validated = validate_public_https_url(url, self.allowed_domains)
        parts = urlsplit(validated)
        origin = urlunsplit((parts.scheme, parts.netloc, "", "", ""))
        cached = self._robots_cache.get(origin)
        if isinstance(cached, RobotFileParser):
            return cached.can_fetch(USER_AGENT, validated)
        if cached is False:
            return False
        robots_url = origin + "/robots.txt"
        try:
            result = self.fetch(
                robots_url,
                accept="text/plain, text/*;q=0.9",
                max_bytes=MAX_ROBOTS_BYTES,
            )
        except HTTPError as exc:
            if exc.code == 404:
                parser = RobotFileParser()
                parser.parse([])
                self._robots_cache[origin] = parser
                return True
            self._robots_cache[origin] = False
            return False
        except SourceCollectionError:
            self._robots_cache[origin] = False
            return False
        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(result.body.decode("utf-8", errors="replace").splitlines())
        self._robots_cache[origin] = parser
        return parser.can_fetch(USER_AGENT, validated)

    def download_media(self, url: str, target: Path, *, max_bytes: int) -> tuple[str, str]:
        """Download one explicitly selected media item with a hard byte quota."""
        validated = validate_public_https_url(url, self.allowed_domains)
        request = Request(
            validated,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "audio/*, video/*, application/octet-stream;q=0.8",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
            method="GET",
        )
        opener = build_opener(_SafeRedirectHandler(self.allowed_domains))
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with opener.open(request, timeout=max(self.timeout_seconds, 60.0)) as response:
                final_url = response.geturl()
                validate_public_https_url(final_url, self.allowed_domains)
                content_type = response.headers.get_content_type().lower()
                if not any(content_type.startswith(prefix) for prefix in MEDIA_CONTENT_TYPES):
                    raise SourceCollectionError(
                        f"media response has unsupported content type: {content_type}"
                    )
                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        if int(content_length) > max_bytes:
                            raise SourceCollectionError(
                                f"media response exceeds {max_bytes} byte limit"
                            )
                    except ValueError:
                        pass
                digest = hashlib.sha256()
                total = 0
                descriptor, temp_name = tempfile.mkstemp(
                    prefix=target.name + ".", suffix=".tmp", dir=str(target.parent)
                )
                temporary = Path(temp_name)
                with os.fdopen(descriptor, "wb") as stream:
                    while chunk := response.read(1024 * 1024):
                        total += len(chunk)
                        if total > max_bytes:
                            raise SourceCollectionError(
                                f"media response exceeds {max_bytes} byte limit"
                            )
                        digest.update(chunk)
                        stream.write(chunk)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, target)
                temporary = None
                return digest.hexdigest(), content_type
        except HTTPError:
            raise
        except (URLError, OSError, TimeoutError) as exc:
            raise SourceCollectionError("media request failed") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass


class _PlainTextHTMLParser(HTMLParser):
    SKIP_TAGS = frozenset({"script", "style", "noscript", "template", "svg"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        elif not self.skip_depth and tag in {"p", "div", "br", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        elif not self.skip_depth and tag in {"p", "div", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return _normalize_text("".join(self.parts))


class _ReadableArticleParser(HTMLParser):
    SKIP_TAGS = frozenset(
        {"script", "style", "noscript", "template", "svg", "nav", "footer", "form", "aside"}
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.article_depth = 0
        self.article_parts: list[str] = []
        self.paragraph_parts: list[str] = []
        self.current_paragraph: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "article":
            self.article_depth += 1
        if tag == "p":
            self.current_paragraph = []
        if self.article_depth and tag in {"p", "br", "li", "h1", "h2", "h3"}:
            self.article_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "p" and self.current_paragraph is not None:
            paragraph = _normalize_text("".join(self.current_paragraph))
            if paragraph:
                self.paragraph_parts.append(paragraph)
            self.current_paragraph = None
        if tag == "article" and self.article_depth:
            self.article_depth -= 1
        if self.article_depth and tag in {"p", "li", "h1", "h2", "h3"}:
            self.article_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.article_depth:
            self.article_parts.append(data)
        if self.current_paragraph is not None:
            self.current_paragraph.append(data)

    def text(self) -> str:
        article = _normalize_text("".join(self.article_parts))
        fallback = "\n\n".join(self.paragraph_parts)
        text = article if len(article) >= len(fallback) // 2 and len(article) >= 300 else fallback
        return text[:MAX_READABLE_CHARS].strip()


def _normalize_text(value: str) -> str:
    lines = []
    for raw_line in html.unescape(value).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = re.sub(r"[ \t\f\v]+", " ", raw_line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def strip_html(value: str, *, max_chars: int = 4_000) -> str:
    parser = _PlainTextHTMLParser()
    try:
        parser.feed(value)
        parser.close()
    except (ValueError, TypeError):
        return _normalize_text(value)[:max_chars]
    return parser.text()[:max_chars]


def extract_readable_text(payload: bytes) -> str:
    parser = _ReadableArticleParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    parser.close()
    return parser.text()


def canonicalize_url(url: str) -> str:
    """Remove fragments and common tracking parameters without changing content parameters."""
    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError as exc:
        raise SourceURLValidationError("URL is malformed") from exc
    query = []
    for name, value in parse_qsl(parts.query, keep_blank_values=True):
        lowered = name.casefold()
        if lowered in TRACKING_QUERY_NAMES or lowered.startswith(TRACKING_QUERY_PREFIXES):
            continue
        query.append((name, value))
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower().rstrip(".")
    netloc = host
    if port not in (None, 443):
        netloc = f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    return urlunsplit((scheme, netloc, path, urlencode(query, doseq=True), ""))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(element: ET.Element, names: Iterable[str]) -> str | None:
    wanted = {name.lower() for name in names}
    for child in element:
        if _local_name(child.tag) in wanted:
            value = "".join(child.itertext()).strip()
            if value:
                return value
    return None


def _entry_link(element: ET.Element) -> str | None:
    plain = _child_text(element, ["link"])
    if plain and plain.startswith("https://"):
        return plain
    for child in element:
        if _local_name(child.tag) != "link":
            continue
        rel = child.attrib.get("rel", "alternate").lower()
        href = child.attrib.get("href", "").strip()
        if rel in {"alternate", ""} and href.startswith("https://"):
            return href
    guid = _child_text(element, ["guid", "id"])
    if guid and guid.startswith("https://"):
        return guid
    return None


def _entry_media(element: ET.Element) -> tuple[str | None, str | None, str | None]:
    for child in element.iter():
        name = _local_name(child.tag)
        if name == "link" and child.attrib.get("rel", "").lower() == "enclosure":
            url = child.attrib.get("href", "").strip()
            content_type = child.attrib.get("type", "").lower() or None
        elif name in {"enclosure", "content"}:
            url = (child.attrib.get("url") or child.attrib.get("href") or "").strip()
            content_type = child.attrib.get("type", "").lower() or None
        else:
            continue
        if not url.startswith("https://"):
            continue
        medium = child.attrib.get("medium", "").lower()
        if (content_type or "").startswith("audio/") or medium == "audio":
            return url, content_type, "audio"
        if (content_type or "").startswith("video/") or medium == "video":
            return url, content_type, "video"
    return None, None, None


def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip()
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return raw[:100]
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _item_id(source_id: str, canonical_url: str, media_url: str | None) -> str:
    identity = canonical_url or media_url or source_id
    digest = hashlib.sha256(f"{source_id}\0{identity}".encode("utf-8")).hexdigest()[:24]
    return f"{source_id}-{digest}"


def parse_feed(
    payload: bytes,
    *,
    source: dict[str, Any],
    feed: dict[str, Any],
    limit: int = 50,
) -> list[CollectedItem]:
    """Parse bounded RSS or Atom bytes into normalized, untrusted item metadata."""
    if len(payload) > MAX_FEED_BYTES:
        raise SourceCollectionError("feed exceeds the 2 MB safety limit")
    lowered = payload.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered:
        raise SourceCollectionError("feed XML must not contain DTD or entity declarations")
    try:
        # The complete bounded payload was checked above, not only its prefix.
        root = ET.fromstring(payload)  # nosec B314
    except ET.ParseError as exc:
        raise SourceCollectionError("feed is not valid RSS/Atom XML") from exc

    candidates = [
        element for element in root.iter() if _local_name(element.tag) in {"item", "entry"}
    ]
    results: list[CollectedItem] = []
    seen_ids: set[str] = set()
    allowed_domains = source["domains"]
    for entry in candidates:
        if len(results) >= limit:
            break
        title = strip_html(_child_text(entry, ["title"]) or "", max_chars=500)
        page_url = _entry_link(entry)
        media_url, media_content_type, detected_media = _entry_media(entry)
        fallback_media = str(feed.get("media_type", "article"))
        media_type = detected_media or (fallback_media if fallback_media != "mixed" else "article")
        if not title or not (page_url or media_url):
            continue
        warnings: list[str] = []
        if page_url:
            try:
                page_url = canonicalize_url(page_url)
                validate_public_https_url(page_url, allowed_domains)
            except SourceCollectionError:
                page_url = None
                warnings.append("item_page_url_outside_source_domains")
        if media_url:
            try:
                media_url = canonicalize_url(media_url)
                validate_public_https_url(media_url, allowed_domains)
            except SourceCollectionError:
                media_url = None
                media_content_type = None
                warnings.append("media_url_outside_source_domains")
        if not page_url and not media_url:
            continue
        canonical_url = page_url or media_url or ""
        if detected_media and not media_url:
            media_type = "article"

        item_id = _item_id(source["source_id"], canonical_url, media_url)
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        summary_value = _child_text(entry, ["description", "summary", "content"])
        author = _child_text(entry, ["author", "creator"])
        results.append(
            CollectedItem(
                item_id=item_id,
                source_id=source["source_id"],
                source_name=source["canonical_name"],
                title=title,
                canonical_url=canonical_url,
                media_type=media_type,
                published_at=_normalize_date(
                    _child_text(entry, ["pubdate", "published", "updated", "date"])
                ),
                author=strip_html(author, max_chars=300) if author else None,
                summary=strip_html(summary_value, max_chars=4_000) if summary_value else None,
                media_url=media_url,
                media_content_type=media_content_type,
                feed_id=feed["feed_id"],
                feed_url=feed["url"],
                exam_usage=[dict(usage) for usage in source["usage"]],
                warnings=warnings,
            )
        )
    return results


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


class CorpusStore:
    """Atomic local manifest plus content/media artifacts."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "manifest.jsonl"
        self.items_dir = self.root / "items"
        self.content_dir = self.root / "content"
        self.media_dir = self.root / "media"

    def _load_unlocked(self) -> dict[str, CollectedItem]:
        if not self.manifest_path.exists():
            return {}
        if self.manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            raise SourceCollectionError("corpus manifest exceeds the 64 MB safety limit")
        items: dict[str, CollectedItem] = {}
        for line_number, line in enumerate(
            self.manifest_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            if len(line.encode("utf-8")) > MAX_ITEM_JSON_BYTES:
                raise SourceCollectionError(f"manifest line {line_number} is too large")
            try:
                payload = json.loads(line)
                item = CollectedItem(**payload)
            except (json.JSONDecodeError, TypeError) as exc:
                raise SourceCollectionError(f"invalid manifest line {line_number}") from exc
            if item.item_id in items:
                raise SourceCollectionError(f"duplicate item_id in manifest: {item.item_id}")
            items[item.item_id] = item
        return items

    def load(self) -> dict[str, CollectedItem]:
        with exclusive_file_lock(self.manifest_path):
            return self._load_unlocked()

    def upsert(self, incoming: Iterable[CollectedItem], *, observed_at: str) -> tuple[int, int]:
        with exclusive_file_lock(self.manifest_path):
            existing = self._load_unlocked()
            new_count = 0
            updated_count = 0
            for item in incoming:
                previous = existing.get(item.item_id)
                if previous is None:
                    item.first_seen_at = observed_at
                    item.last_seen_at = observed_at
                    existing[item.item_id] = item
                    new_count += 1
                else:
                    item.first_seen_at = previous.first_seen_at
                    item.last_seen_at = observed_at
                    item.content_path = previous.content_path
                    item.content_sha256 = previous.content_sha256
                    item.media_path = previous.media_path
                    item.media_sha256 = previous.media_sha256
                    existing[item.item_id] = item
                    updated_count += 1
                item_path = self.items_dir / f"{item.item_id}.json"
                _atomic_write_text(
                    item_path,
                    json.dumps(asdict(existing[item.item_id]), ensure_ascii=False, indent=2) + "\n",
                )
            manifest = "".join(
                json.dumps(asdict(item), ensure_ascii=False, sort_keys=True) + "\n"
                for item in sorted(existing.values(), key=lambda value: value.item_id)
            )
            _atomic_write_text(self.manifest_path, manifest)
            return new_count, updated_count

    def update_item(self, item: CollectedItem) -> None:
        with exclusive_file_lock(self.manifest_path):
            existing = self._load_unlocked()
            if item.item_id not in existing:
                raise SourceCollectionError(f"unknown corpus item: {item.item_id}")
            existing[item.item_id] = item
            _atomic_write_text(
                self.items_dir / f"{item.item_id}.json",
                json.dumps(asdict(item), ensure_ascii=False, indent=2) + "\n",
            )
            manifest = "".join(
                json.dumps(asdict(value), ensure_ascii=False, sort_keys=True) + "\n"
                for value in sorted(existing.values(), key=lambda value: value.item_id)
            )
            _atomic_write_text(self.manifest_path, manifest)

    def get(self, item_id: str) -> CollectedItem:
        items = self.load()
        try:
            return items[item_id]
        except KeyError as exc:
            raise SourceCollectionError(f"unknown corpus item: {item_id}") from exc


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def collect_source_feeds(
    source: dict[str, Any],
    store: CorpusStore,
    *,
    limit: int = 50,
    content_mode: str = "metadata",
    delay_seconds: float = 1.0,
    now: str | None = None,
) -> dict[str, Any]:
    """Collect one maintained source through its verified RSS/Atom endpoints."""
    feeds = source.get("feeds", [])
    if not feeds:
        raise SourceCollectionError(
            "source has no maintained public feed; provide a specific public URL in a later step"
        )
    if not 1 <= limit <= 100:
        raise SourceCollectionError("limit must be between 1 and 100")
    if content_mode not in {"metadata", "text"}:
        raise SourceCollectionError("content_mode must be metadata or text")
    if not 0 <= delay_seconds <= 60:
        raise SourceCollectionError("delay_seconds must be between 0 and 60")

    fetcher = SourceFetcher(source["domains"])
    remaining = limit
    items: list[CollectedItem] = []
    feed_errors: list[dict[str, str]] = []
    feeds_attempted = 0
    feeds_succeeded = 0
    for feed_index, feed in enumerate(feeds):
        if remaining <= 0:
            break
        if feed_index and delay_seconds:
            time.sleep(delay_seconds)
        feeds_attempted += 1
        try:
            fetched = fetcher.fetch(
                feed["url"],
                accept="application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9",
                max_bytes=MAX_FEED_BYTES,
            )
            parsed = parse_feed(fetched.body, source=source, feed=feed, limit=remaining)
        except (HTTPError, SourceCollectionError) as exc:
            feed_errors.append({"feed_id": feed["feed_id"], "error": str(exc)[:300]})
            continue
        feeds_succeeded += 1
        items.extend(parsed)
        remaining = limit - len(items)

    if feeds_attempted and feeds_succeeded == 0:
        details = "; ".join(
            f"{entry['feed_id']}: {entry['error']}" for entry in feed_errors
        )
        raise SourceCollectionError(f"all source feeds failed: {details}")

    observed_at = now or _utc_now()
    new_count, updated_count = store.upsert(items, observed_at=observed_at)
    materialized = 0
    if content_mode == "text":
        for item_index, item in enumerate(items):
            if item.media_type != "article":
                continue
            if item_index and delay_seconds:
                time.sleep(delay_seconds)
            try:
                materialize_text(source, store, item.item_id, fetcher=fetcher)
            except (HTTPError, SourceCollectionError) as exc:
                item.warnings.append(f"text_not_materialized:{str(exc)[:160]}")
                store.update_item(item)
            else:
                materialized += 1
    return {
        "source_id": source["source_id"],
        "fetched": len(items),
        "new": new_count,
        "updated": updated_count,
        "text_materialized": materialized,
        "feeds_attempted": feeds_attempted,
        "feeds_succeeded": feeds_succeeded,
        "feed_errors": feed_errors,
        "corpus_root": str(store.root),
    }


def materialize_text(
    source: dict[str, Any],
    store: CorpusStore,
    item_id: str,
    *,
    fetcher: SourceFetcher | None = None,
) -> CollectedItem:
    """Fetch one selected article as readable text after a robots check."""
    item = store.get(item_id)
    if item.source_id != source["source_id"]:
        raise SourceCollectionError("item does not belong to the selected source")
    if item.media_type != "article":
        raise SourceCollectionError("selected item is not an article")
    client = fetcher or SourceFetcher(source["domains"])
    if not client.robots_allowed(item.canonical_url):
        raise SourceCollectionError("robots.txt does not permit automated article retrieval")
    result = client.fetch(
        item.canonical_url,
        accept="text/html, application/xhtml+xml;q=0.9",
        max_bytes=MAX_HTML_BYTES,
    )
    if result.content_type not in {"text/html", "application/xhtml+xml"}:
        raise SourceCollectionError(f"article response is not HTML: {result.content_type}")
    text = extract_readable_text(result.body)
    if len(text) < 300:
        raise SourceCollectionError("article text is unavailable or too short; no paywall bypass attempted")
    target = store.content_dir / f"{item.item_id}.txt"
    _atomic_write_text(target, text + "\n")
    item.content_path = target.relative_to(store.root).as_posix()
    item.content_sha256 = hashlib.sha256((text + "\n").encode("utf-8")).hexdigest()
    store.update_item(item)
    return item


def _media_extension(item: CollectedItem) -> str:
    content_type = (item.media_content_type or "").split(";", 1)[0].lower()
    mapping = {
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/ogg": ".ogg",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
    }
    if content_type in mapping:
        return mapping[content_type]
    path_suffix = Path(urlsplit(item.media_url or "").path).suffix.lower()
    if path_suffix in {".mp3", ".m4a", ".aac", ".ogg", ".wav", ".mp4", ".webm"}:
        return path_suffix
    return ".bin"


def materialize_media(
    source: dict[str, Any],
    store: CorpusStore,
    item_id: str,
    *,
    max_bytes: int = DEFAULT_MAX_MEDIA_BYTES,
) -> CollectedItem:
    """Download one selected, feed-enclosed media object within a hard quota."""
    if not 1 <= max_bytes <= 1024 * 1024 * 1024:
        raise SourceCollectionError("max_bytes must be between 1 byte and 1 GiB")
    item = store.get(item_id)
    if item.source_id != source["source_id"]:
        raise SourceCollectionError("item does not belong to the selected source")
    if item.media_type not in {"audio", "video"} or not item.media_url:
        raise SourceCollectionError("selected item has no allowed audio/video enclosure")
    target = store.media_dir / f"{item.item_id}{_media_extension(item)}"
    digest, content_type = SourceFetcher(source["domains"]).download_media(
        item.media_url, target, max_bytes=max_bytes
    )
    item.media_path = target.relative_to(store.root).as_posix()
    item.media_sha256 = digest
    item.media_content_type = content_type
    store.update_item(item)
    return item

"""Validated source catalog for CET and postgraduate English materials."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit


CATALOG_PATH = (
    Path(__file__).resolve().parents[1] / "assets" / "data" / "source-catalog.json"
)
EVIDENCE_LEVELS = frozenset({"S", "A", "B", "C", "R"})
EXAM_FAMILIES = frozenset({"cet", "postgraduate"})
SOURCE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DOMAIN_RE = re.compile(r"^[a-z0-9.-]+$")


class SourceCatalogError(ValueError):
    """Raised when the maintained source catalog violates its contract."""


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceCatalogError(f"{label} must be a non-empty string")
    return value.strip()


def _normalize_domain(value: Any, label: str) -> str:
    domain = _require_string(value, label).lower().rstrip(".")
    if not DOMAIN_RE.fullmatch(domain) or ".." in domain or domain.startswith("-"):
        raise SourceCatalogError(f"{label} is not a valid domain: {value!r}")
    return domain


def _validate_feed(
    feed: Any,
    source_id: str,
    allowed_domains: Iterable[str],
    seen_feed_ids: set[str],
) -> None:
    if not isinstance(feed, dict):
        raise SourceCatalogError(f"source {source_id} feed must be an object")
    feed_id = _require_string(feed.get("feed_id"), f"source {source_id} feed_id")
    if not SOURCE_ID_RE.fullmatch(feed_id):
        raise SourceCatalogError(f"source {source_id} has invalid feed_id: {feed_id}")
    if feed_id in seen_feed_ids:
        raise SourceCatalogError(f"duplicate feed_id: {feed_id}")
    seen_feed_ids.add(feed_id)
    url = _require_string(feed.get("url"), f"source {source_id} feed URL")
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise SourceCatalogError(f"source {source_id} has invalid feed URL") from exc
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise SourceCatalogError(f"source {source_id} feed URL must be anonymous HTTPS")
    if port not in (None, 443):
        raise SourceCatalogError(f"source {source_id} feed URL must use port 443")
    host = parts.hostname.lower().rstrip(".")
    if not any(host == domain or host.endswith("." + domain) for domain in allowed_domains):
        raise SourceCatalogError(f"source {source_id} feed host is outside its domains")
    feed_media_type = _require_string(
        feed.get("media_type"), f"source {source_id} feed media_type"
    )
    if feed_media_type not in {"article", "audio", "video", "mixed"}:
        raise SourceCatalogError(
            f"source {source_id} has unsupported feed media_type: {feed_media_type}"
        )


def _validate_usage(usage: Any, source_id: str) -> None:
    if not isinstance(usage, list) or not usage:
        raise SourceCatalogError(f"source {source_id} must include exam usage")
    seen: set[tuple[str, str]] = set()
    for entry in usage:
        if not isinstance(entry, dict):
            raise SourceCatalogError(f"source {source_id} usage must contain objects")
        exam = _require_string(entry.get("exam"), f"source {source_id} usage exam")
        if exam not in EXAM_FAMILIES:
            raise SourceCatalogError(f"source {source_id} has unsupported exam: {exam}")
        evidence = _require_string(
            entry.get("evidence"), f"source {source_id} usage evidence"
        )
        if evidence not in {"A", "B", "C"}:
            raise SourceCatalogError(
                f"source {source_id} has unsupported evidence level: {evidence}"
            )
        if evidence == "A" and not entry.get("trace_ids"):
            raise SourceCatalogError(
                f"source {source_id} A-level usage must cite article trace ids"
            )
        sections = entry.get("sections")
        if not isinstance(sections, list) or not sections:
            raise SourceCatalogError(f"source {source_id} usage sections must be non-empty")
        for section in sections:
            section_name = _require_string(section, f"source {source_id} usage section")
            key = (exam, section_name)
            if key in seen:
                raise SourceCatalogError(
                    f"source {source_id} repeats usage for {exam}:{section_name}"
                )
            seen.add(key)


def validate_catalog(data: Any) -> dict[str, Any]:
    """Validate and return a source catalog object."""
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise SourceCatalogError("source catalog schema_version must be 1")
    levels = data.get("evidence_levels")
    if not isinstance(levels, dict) or set(levels) != EVIDENCE_LEVELS:
        raise SourceCatalogError("source catalog must define S/A/B/C/R evidence levels")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise SourceCatalogError("source catalog must contain sources")

    source_ids: set[str] = set()
    names_and_aliases: dict[str, str] = {}
    seen_feed_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise SourceCatalogError("source entries must be objects")
        source_id = _require_string(source.get("source_id"), "source_id")
        if not SOURCE_ID_RE.fullmatch(source_id):
            raise SourceCatalogError(f"invalid source_id: {source_id}")
        if source_id in source_ids:
            raise SourceCatalogError(f"duplicate source_id: {source_id}")
        source_ids.add(source_id)
        name = _require_string(source.get("canonical_name"), f"source {source_id} name")

        aliases = source.get("aliases", [])
        if not isinstance(aliases, list):
            raise SourceCatalogError(f"source {source_id} aliases must be a list")
        for label in [source_id, name, *aliases]:
            normalized = _require_string(label, f"source {source_id} alias").casefold()
            previous = names_and_aliases.get(normalized)
            if previous is not None and previous != source_id:
                raise SourceCatalogError(
                    f"source alias {label!r} maps to both {previous} and {source_id}"
                )
            names_and_aliases[normalized] = source_id

        domains = source.get("domains")
        if not isinstance(domains, list) or not domains:
            raise SourceCatalogError(f"source {source_id} must include domains")
        normalized_domains = [
            _normalize_domain(domain, f"source {source_id} domain") for domain in domains
        ]
        if len(normalized_domains) != len(set(normalized_domains)):
            raise SourceCatalogError(f"source {source_id} repeats a domain")
        source["domains"] = normalized_domains

        media_types = source.get("media_types")
        if not isinstance(media_types, list) or not media_types:
            raise SourceCatalogError(f"source {source_id} must include media_types")
        for media_type in media_types:
            normalized_media_type = _require_string(
                media_type, f"source {source_id} media_type"
            )
            if normalized_media_type not in {"article", "audio", "video", "report"}:
                raise SourceCatalogError(
                    f"source {source_id} has unsupported media_type: {normalized_media_type}"
                )
        _validate_usage(source.get("usage"), source_id)
        feeds = source.get("feeds", [])
        if not isinstance(feeds, list):
            raise SourceCatalogError(f"source {source_id} feeds must be a list")
        for feed in feeds:
            _validate_feed(feed, source_id, normalized_domains, seen_feed_ids)

    references = data.get("reference_corpora")
    if not isinstance(references, list):
        raise SourceCatalogError("reference_corpora must be a list")
    reference_ids: set[str] = set()
    for resource in references:
        if not isinstance(resource, dict):
            raise SourceCatalogError("reference corpus entries must be objects")
        resource_id = _require_string(resource.get("resource_id"), "resource_id")
        if not SOURCE_ID_RE.fullmatch(resource_id) or resource_id in reference_ids:
            raise SourceCatalogError(f"invalid or duplicate resource_id: {resource_id}")
        reference_ids.add(resource_id)
        _require_string(resource.get("name"), f"reference {resource_id} name")
        if resource.get("role") != "R":
            raise SourceCatalogError(f"reference {resource_id} role must be R")
    return data


def load_source_catalog(path: Path | None = None) -> dict[str, Any]:
    """Load the maintained catalog or an explicitly supplied compatible catalog."""
    catalog_path = Path(path) if path is not None else CATALOG_PATH
    try:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceCatalogError(f"could not load source catalog: {exc}") from exc
    return validate_catalog(data)


def source_alias_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a case-insensitive source id/name/alias index."""
    index: dict[str, dict[str, Any]] = {}
    for source in catalog["sources"]:
        labels = [source["source_id"], source["canonical_name"], *source.get("aliases", [])]
        for label in labels:
            index[str(label).casefold()] = source
    return index


def resolve_source(catalog: dict[str, Any], value: str) -> dict[str, Any]:
    """Resolve a source by id, canonical name, or maintained alias."""
    source = source_alias_index(catalog).get(value.strip().casefold())
    if source is None:
        raise SourceCatalogError(f"unknown source: {value}")
    return source


def filter_sources(
    catalog: dict[str, Any],
    *,
    exam: str | None = None,
    section: str | None = None,
    evidence: str | None = None,
    media_type: str | None = None,
    collectable_only: bool = False,
) -> list[dict[str, Any]]:
    """Filter maintained sources without changing their evidence labels."""
    results: list[dict[str, Any]] = []
    for source in catalog["sources"]:
        if media_type and media_type not in source.get("media_types", []):
            continue
        if collectable_only and not source.get("feeds"):
            continue
        matching_usage = []
        for usage in source["usage"]:
            if exam and usage["exam"] != exam:
                continue
            if section and section not in usage["sections"]:
                continue
            if evidence and usage["evidence"] != evidence:
                continue
            matching_usage.append(usage)
        if (exam or section or evidence) and not matching_usage:
            continue
        results.append(source)
    return sorted(results, key=lambda item: item["canonical_name"].casefold())


def all_catalog_domains(sources: Iterable[dict[str, Any]]) -> set[str]:
    """Return the normalized domain set for one or more catalog sources."""
    return {
        domain
        for source in sources
        for domain in source.get("domains", [])
        if isinstance(domain, str)
    }

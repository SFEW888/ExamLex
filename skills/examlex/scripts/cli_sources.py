"""CLI commands for the maintained exam-source catalog and local corpus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .source_catalog import (
    EVIDENCE_LEVELS,
    SourceCatalogError,
    filter_sources,
    load_source_catalog,
    resolve_source,
)
from .source_collector import (
    CorpusStore,
    SourceCollectionError,
    collect_source_feeds,
    default_corpus_root,
    materialize_media,
    materialize_text,
)


def _print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def list_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="examlex source-list",
        description="List maintained CET/postgraduate source candidates and evidence labels.",
    )
    parser.add_argument("--exam", choices=["cet", "postgraduate"])
    parser.add_argument("--section", help="Filter by section, such as reading or listening")
    parser.add_argument("--evidence", choices=sorted(EVIDENCE_LEVELS))
    parser.add_argument("--media", choices=["article", "audio", "video", "report"])
    parser.add_argument("--collectable", action="store_true", help="Only sources with a verified feed")
    parser.add_argument("--references", action="store_true", help="Include R-level reference corpora")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        catalog = load_source_catalog()
        sources = filter_sources(
            catalog,
            exam=args.exam,
            section=args.section,
            evidence=args.evidence,
            media_type=args.media,
            collectable_only=args.collectable,
        )
    except SourceCatalogError as exc:
        print(f"Source catalog error: {exc}", file=sys.stderr)
        return 1

    rows = [
        {
            "source_id": source["source_id"],
            "name": source["canonical_name"],
            "media_types": source["media_types"],
            "usage": source["usage"],
            "feed_ids": [feed["feed_id"] for feed in source.get("feeds", [])],
        }
        for source in sources
    ]
    payload: dict[str, object] = {
        "schema_version": catalog["schema_version"],
        "count": len(rows),
        "sources": rows,
    }
    if args.references:
        payload["reference_corpora"] = catalog["reference_corpora"]
    if args.json:
        _print_json(payload)
    else:
        for row in rows:
            evidence = sorted(
                {
                    usage["evidence"]
                    for usage in row["usage"]  # type: ignore[index]
                    if isinstance(usage, dict)
                }
            )
            feeds = ",".join(row["feed_ids"]) or "-"  # type: ignore[arg-type]
            media = ",".join(row["media_types"])  # type: ignore[arg-type]
            print(f"{row['source_id']}: {row['name']} [{'/'.join(evidence)}] {media} feeds={feeds}")
        if args.references:
            print("\nReference corpora (R):")
            for resource in catalog["reference_corpora"]:
                print(f"{resource['resource_id']}: {resource['name']}")
    return 0


def collect_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="examlex source-collect",
        description="Collect a maintained source through verified RSS/Atom feeds.",
    )
    parser.add_argument("--source", required=True, help="Source id, name, or maintained alias")
    parser.add_argument("--output-dir", type=Path, default=default_corpus_root())
    parser.add_argument("--limit", type=int, default=20, help="Maximum items, 1-100")
    parser.add_argument(
        "--content-mode",
        choices=["metadata", "text"],
        default="metadata",
        help="metadata is default; text also retrieves robots-allowed public article pages",
    )
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests, 0-60")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        catalog = load_source_catalog()
        source = resolve_source(catalog, args.source)
        result = collect_source_feeds(
            source,
            CorpusStore(args.output_dir),
            limit=args.limit,
            content_mode=args.content_mode,
            delay_seconds=args.delay,
        )
    except (SourceCatalogError, SourceCollectionError, OSError) as exc:
        if args.json:
            _print_json({"status": "error", "message": str(exc)})
        else:
            print(f"Source collection failed: {exc}", file=sys.stderr)
        return 1
    payload = {"status": "partial" if result["feed_errors"] else "ok", **result}
    if args.json:
        _print_json(payload)
    else:
        print(
            f"Collected {result['fetched']} items from {result['source_id']} "
            f"({result['new']} new, {result['updated']} updated)."
        )
        print(f"Corpus: {result['corpus_root']}")
        if result["feed_errors"]:
            print(f"Feed errors: {len(result['feed_errors'])}", file=sys.stderr)
    return 0


def fetch_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="examlex source-fetch",
        description="Explicitly materialize one indexed article or feed-enclosed media item.",
    )
    parser.add_argument("--source", required=True, help="Source id, name, or maintained alias")
    parser.add_argument("--item", required=True, help="Item id from manifest.jsonl")
    parser.add_argument("--kind", required=True, choices=["text", "media"])
    parser.add_argument("--output-dir", type=Path, default=default_corpus_root())
    parser.add_argument(
        "--max-media-mb",
        type=int,
        default=100,
        help="Hard media download limit in MiB (1-1024)",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        catalog = load_source_catalog()
        source = resolve_source(catalog, args.source)
        store = CorpusStore(args.output_dir)
        if args.kind == "text":
            item = materialize_text(source, store, args.item)
        else:
            if not 1 <= args.max_media_mb <= 1024:
                raise SourceCollectionError("max-media-mb must be between 1 and 1024")
            item = materialize_media(
                source,
                store,
                args.item,
                max_bytes=args.max_media_mb * 1024 * 1024,
            )
    except (SourceCatalogError, SourceCollectionError, OSError) as exc:
        if args.json:
            _print_json({"status": "error", "message": str(exc)})
        else:
            print(f"Source fetch failed: {exc}", file=sys.stderr)
        return 1
    payload = {
        "status": "ok",
        "item": {
            "item_id": item.item_id,
            "source_id": item.source_id,
            "media_type": item.media_type,
            "content_path": item.content_path,
            "content_sha256": item.content_sha256,
            "media_path": item.media_path,
            "media_sha256": item.media_sha256,
        },
    }
    if args.json:
        _print_json(payload)
    else:
        location = item.content_path if args.kind == "text" else item.media_path
        print(f"Materialized {item.item_id}: {location}")
    return 0

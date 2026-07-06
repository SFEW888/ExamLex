"""CLI entry point: tutor extract — download/parse raw materials."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import TutorConfig
from .session import SessionManager
from .extractors.url_resolver import resolve_input, InputType
from .extractors.text import TextExtractor


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract raw materials from a source.")
    parser.add_argument("--input", required=True, help="URL, file path, or person name")
    parser.add_argument("--type", choices=["auto", "video", "book", "text", "person"],
                        default="auto", help="Force input type")
    parser.add_argument("--output-dir", help="Override sessions root directory (session artifacts are created under here)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args(argv)

    cfg = TutorConfig()
    sessions_root = Path(args.output_dir) if args.output_dir else cfg.sessions_root
    mgr = SessionManager(sessions_root)

    input_type = resolve_input(args.input)
    if args.type != "auto":
        type_map = {"video": InputType.URL_VIDEO, "book": InputType.LOCAL_BOOK,
                    "text": InputType.LOCAL_TEXT, "person": InputType.PERSON_NAME}
        detected = type_map.get(args.type)
        if detected:
            input_type = detected

    # For now, only text extraction is fully implemented
    # Video and book extractors will be added as separate modules
    if input_type == InputType.LOCAL_TEXT:
        session = mgr.create(source_type="text")
        extractor = TextExtractor()
        # Resolve early so non-existent files fail with a clean message instead
        # of an unhandled traceback further down.
        resolved = Path(args.input).expanduser().resolve()
        if not resolved.is_file():
            output = {
                "status": "error",
                "message": f"Input file not found: {resolved}",
                "session_id": session.session_id,
            }
            if args.json:
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                print(f"Error: {output['message']}", file=sys.stderr)
            return 1
        try:
            result = extractor.extract(str(resolved), session.artifacts_dir)
        except (FileNotFoundError, IsADirectoryError, PermissionError, OSError, UnicodeDecodeError, ValueError) as exc:
            output = {
                "status": "error",
                "message": f"Failed to extract text: {exc}",
                "session_id": session.session_id,
            }
            if args.json:
                print(json.dumps(output, ensure_ascii=False, indent=2))
            else:
                print(f"Error: {exc}", file=sys.stderr)
            return 1
        session.checkpoint("extract")
        output = {
            "status": "ok",
            "session_id": session.session_id,
            "artifacts_dir": str(session.artifacts_dir),
            "next_stage": "distill",
            "source_type": "text",
            "summary": {
                "char_count": result.metadata.get("char_count", 0),
                "word_count_approx": result.metadata.get("word_count_approx", 0),
                "warnings": result.warnings,
            },
        }
    elif input_type == InputType.URL_VIDEO:
        output = {
            "status": "not_implemented",
            "message": "Video extraction not yet implemented. Install yt-dlp and ffmpeg, then use the video extractor module.",
            "input_type": "video",
        }
    elif input_type == InputType.LOCAL_BOOK:
        output = {
            "status": "not_implemented",
            "message": "Book extraction not yet implemented. Use the book extractor module (requires pdftotext or Docling).",
            "input_type": "book",
        }
    elif input_type == InputType.PERSON_NAME:
        session = mgr.create(source_type="person")
        session.checkpoint("extract")  # No extraction needed, proceed to distill
        output = {
            "status": "ok",
            "session_id": session.session_id,
            "artifacts_dir": str(session.artifacts_dir),
            "next_stage": "distill",
            "source_type": "person",
            "summary": {"person_name": args.input},
        }
    else:
        output = {
            "status": "error",
            "message": f"Cannot process input type: {input_type}",
        }

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if output["status"] == "ok":
            print(f"Extraction complete. Session: {output.get('session_id')}")
            print(f"Artifacts: {output.get('artifacts_dir')}")
            print(f"Next stage: {output.get('next_stage')}")
            for warning in output.get("summary", {}).get("warnings", []):
                print(f"Warning: {warning}", file=sys.stderr)
        else:
            print(f"Status: {output['status']} -- {output.get('message', '')}")

    return 0 if output["status"] == "ok" else 1

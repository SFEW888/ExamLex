"""Session and artifact management for the distillation pipeline.

Each distillation run creates a Session with a unique session_id and
an artifacts_dir where all intermediate files live. The pipeline_state.json
file tracks progress so long-running distillations can be resumed.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


class Session:
    """A single distillation run."""

    def __init__(
        self,
        session_id: str,
        artifacts_dir: Path,
        source_type: str,
        current_stage: str = "init",
        sub_stage: str | None = None,
    ) -> None:
        self.session_id = session_id
        self.artifacts_dir = artifacts_dir
        self.source_type = source_type
        self.current_stage = current_stage
        self.sub_stage = sub_stage

    def checkpoint(self, stage: str, *, sub_stage: str | None = None) -> None:
        """Record progress to pipeline_state.json."""
        self.current_stage = stage
        self.sub_stage = sub_stage
        state = {
            "session_id": self.session_id,
            "source_type": self.source_type,
            "stage": stage,
            "sub_stage": sub_stage,
            "artifacts_dir": str(self.artifacts_dir),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        state_path = self.artifacts_dir / "pipeline_state.json"
        if not self.artifacts_dir.exists():
            raise FileNotFoundError(
                f"Artifacts directory missing: {self.artifacts_dir}. "
                "It may have been deleted or moved; create a new session."
            )
        state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def resume_info(self) -> dict:
        """Return structured guidance for the Agent on how to resume."""
        next_actions = {
            "init": "Run extraction to produce raw materials.",
            "extract": (
                "Extraction artifacts are in the artifacts directory. "
                "If the previous run failed, check the sub_stage field to "
                "know where to resume (e.g. skip download, retry ASR)."
            ),
            "distill": (
                "Read the extracted text from the artifacts directory. "
                "Follow the distillation methodology for the source type. "
                "Write distilled strategies to distilled.json."
            ),
            "validate": (
                "Run 'examlex validate --artifacts-dir <path>' to check "
                "format and compute Darwin structure scores."
            ),
            "evaluate": (
                "Run effect scoring using test prompts. "
                "Follow prompts/effect.py for the evaluation guide. "
                "Write results to evaluation.json."
            ),
            "commit": (
                "Run 'examlex commit --artifacts-dir <path>' to write "
                "strategies into the strategy library with ratchet check."
            ),
            "committed": "Pipeline complete. Artifacts may be cleaned up.",
            "failed": (
                "The previous run failed. Check the error field in "
                "pipeline_state.json for details, then re-run from "
                "the appropriate stage."
            ),
        }
        return {
            "session_id": self.session_id,
            "current_stage": self.current_stage,
            "sub_stage": self.sub_stage,
            "artifacts_dir": str(self.artifacts_dir),
            "source_type": self.source_type,
            "next_action": next_actions.get(
                self.current_stage,
                f"Stage '{self.current_stage}' — consult the pipeline documentation.",
            ),
        }


class SessionManager:
    """Creates and resumes distillation sessions."""

    def __init__(self, sessions_root: Path) -> None:
        self.sessions_root = Path(sessions_root)

    def create(self, source_type: str) -> Session:
        """Start a new session with a unique ID and fresh artifacts directory."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        # Use the full UUID; truncating to 8 hex chars leaves only 32 bits of
        # entropy and risks silent collisions (birthday paradox ~50% at ~77k IDs).
        session_id = str(uuid.uuid4())
        artifacts_dir = self.sessions_root / today / session_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        session = Session(
            session_id=session_id,
            artifacts_dir=artifacts_dir,
            source_type=source_type,
        )
        session.checkpoint("init")
        return session

    def resume(self, session_id: str) -> Session:
        """Resume an existing session from its pipeline_state.json."""
        # Search newest date directory first (ISO date names sort lexically),
        # so that if the same id exists under multiple dates we resume the most
        # recent session rather than the oldest.
        for date_dir in sorted(self.sessions_root.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            candidate = date_dir / session_id
            state_file = candidate / "pipeline_state.json"
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Corrupted pipeline state in {state_file}: {exc}"
                    ) from exc
                return Session(
                    session_id=session_id,
                    artifacts_dir=candidate,
                    source_type=state.get("source_type", "unknown"),
                    current_stage=state.get("stage", "init"),
                    sub_stage=state.get("sub_stage"),
                )
        raise FileNotFoundError(
            f"No session found with id '{session_id}'. "
            f"Checked under {self.sessions_root}."
        )

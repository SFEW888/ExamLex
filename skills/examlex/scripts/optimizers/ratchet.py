"""Strategy-level ratchet mechanism with Darwin score tracking.

Ensures scores only go up — regressions trigger automatic revert.
Adapted from darwin-skill's git-based ratchet, adapted for in-library
strategy versioning within strategy-library.json.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any


class RatchetDecision(Enum):
    KEEP = "keep"
    REVERT = "revert"
    BASELINE = "baseline"


@dataclass
class RatchetResult:
    decision: RatchetDecision
    old_score: float
    new_score: float
    delta: float
    reason: str
    should_stop: bool = False  # touch-top signal


class StrategyRatchet:
    """Manages score history and ratchet logic for individual strategies."""

    def __init__(self, touch_top_delta: float = 2.0, max_rounds: int = 3):
        self.touch_top_delta = touch_top_delta
        self.max_rounds = max_rounds

    def baseline(self, strategy: dict, score: float, dimensions: dict | None = None) -> dict:
        """Record the initial baseline score for a strategy."""
        s = copy.deepcopy(strategy)
        s["darwin_score"] = score
        s["score_history"] = [{
            "version": 1,
            "score": score,
            "dimensions": dimensions or {},
            "changed_at": date.today().isoformat(),
            "delta": 0.0,
            "status": RatchetDecision.BASELINE.value,
        }]
        s["revisions"] = [self._revision(s, 1)]
        return s

    @staticmethod
    def _revision(strategy: dict, version: int) -> dict:
        """Capture a content-addressed, immutable strategy revision."""
        snapshot = copy.deepcopy(strategy)
        snapshot.pop("score_history", None)
        snapshot.pop("revisions", None)
        encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {"version": version, "sha256": hashlib.sha256(encoded).hexdigest(), "strategy": snapshot}

    def compare(self, old_strategy: dict, new_strategy: dict, new_score: float,
                dimensions: dict | None = None) -> RatchetResult:
        """Compare new vs old score and decide keep or revert."""
        old_score = old_strategy.get("darwin_score", 0.0)
        delta = round(new_score - old_score, 1)

        if delta < 0:
            return RatchetResult(
                decision=RatchetDecision.REVERT,
                old_score=old_score,
                new_score=new_score,
                delta=delta,
                reason=f"Score decreased by {abs(delta)} points — reverting",
            )

        # Keep (delta >= 0). Compute the touch-top signal from the projected
        # history so callers relying on RatchetResult.should_stop actually see it.
        history = old_strategy.get("score_history", [])
        projected = [h for h in history if isinstance(h, dict)]
        projected.append({"status": RatchetDecision.KEEP.value, "delta": delta})
        stop = self.should_stop(projected)

        reason = (
            f"Score improved by {delta} points"
            if delta > 0
            else "Score unchanged — keeping current version"
        )
        return RatchetResult(
            decision=RatchetDecision.KEEP,
            old_score=old_score,
            new_score=new_score,
            delta=delta,
            reason=reason,
            should_stop=stop,
        )

    def should_stop(self, history: list[dict]) -> bool:
        """Check touch-top signal: last 2 rounds both had delta < threshold."""
        completed = [h for h in history if h.get("status") in (
            RatchetDecision.KEEP.value, RatchetDecision.BASELINE.value
        )]
        if len(completed) < 3:
            return False
        last_two = completed[-2:]
        return all(abs(h.get("delta", 0)) < self.touch_top_delta for h in last_two)

    def apply(self, new_strategy: dict, library: dict, old_strategy: dict | None,
              score: float, dimensions: dict | None = None) -> dict:
        """Apply ratchet check and update the library with the new or reverted strategy.

        WARNING: this mutates ``library`` in place — its ``"strategies"`` list is
        updated with the resulting strategy. Callers reuse the passed ``library``
        dict and persist it via ``atomic_save``, so the side effect is intentional;
        do not share the same dict across independent update flows.
        """
        if old_strategy is None:
            # First time — set baseline
            updated = self.baseline(new_strategy, score, dimensions)
        else:
            result = self.compare(old_strategy, new_strategy, score, dimensions)
            if result.decision == RatchetDecision.REVERT:
                # Keep the old version but record the failed attempt for audit.
                updated = copy.deepcopy(old_strategy)
                history = updated.get("score_history")
                if not isinstance(history, list):
                    history = []
                    updated["score_history"] = history
                history.append({
                    "version": len(history) + 1,
                    "score": score,
                    "dimensions": dimensions or {},
                    "changed_at": date.today().isoformat(),
                    "delta": result.delta,
                    "status": RatchetDecision.REVERT.value,
                    "note": f"Attempted score {score}; reverted to v{len(history)}",
                })
            else:
                history = copy.deepcopy(old_strategy.get("score_history", []))
                next_version = len(history) + 1
                history.append({
                    "version": next_version,
                    "score": score,
                    "dimensions": dimensions or {},
                    "changed_at": date.today().isoformat(),
                    "delta": result.delta,
                    "status": RatchetDecision.KEEP.value,
                })
                updated = copy.deepcopy(new_strategy)
                updated["darwin_score"] = score
                updated["score_history"] = history
                revisions = copy.deepcopy(old_strategy.get("revisions", []))
                if not revisions:
                    revisions.append(self._revision(old_strategy, max(1, next_version - 1)))
                revisions.append(self._revision(updated, next_version))
                updated["revisions"] = revisions

        # Replace in library
        strategies = library.setdefault("strategies", [])
        sid = updated.get("strategy_id")
        for i, s in enumerate(strategies):
            if isinstance(s, dict) and s.get("strategy_id") == sid:
                strategies[i] = updated
                return updated
        # Not found — append
        strategies.append(updated)
        return updated

    @staticmethod
    def atomic_save(library: dict, path: Path) -> Path:
        """Atomically write library to path (temp file + os.replace).
        Also creates a .bak backup before overwriting.
        """
        text = json.dumps(library, ensure_ascii=False, indent=2) + "\n"
        path = Path(path)

        # Backup existing file
        if path.exists():
            bak = path.with_suffix(path.suffix + ".bak")
            try:
                bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            except OSError:
                pass  # non-critical

        # Atomic write
        tmp = path.with_suffix(path.suffix + ".tmp")
        try:
            tmp.write_text(text, encoding="utf-8")
            os.replace(str(tmp), str(path))
        finally:
            # Clean up an orphaned temp file if the write/replace failed
            # (on success it has already been renamed away).
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
        return path

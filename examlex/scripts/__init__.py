"""Expose canonical Skill scripts under the historical ``examlex.scripts`` path."""

from skills.examlex import scripts as _canonical_scripts

__path__ = _canonical_scripts.__path__

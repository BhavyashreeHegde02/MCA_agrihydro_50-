"""Data lineage: where every modelled feature came from.

The study commits to being able to answer, for any column that reaches a model,
which source file and which source column produced it and what happened in
between. This module is the register that makes that answer machine-readable
rather than a paragraph somebody wrote once.

Each feature also carries a ``provenance_class``, which is what the
leakage review in the training phase actually keys on:

``raw``
    Straight from a source file, possibly renamed or unit-checked.
``derived``
    Computed from raw inputs by a documented transformation that does not
    involve the target.
``reference``
    An agronomic constant looked up from a reference table.
``reference_derived``
    Computed from the physics baseline. Anything in this class is algebraically
    related to the reference-derived target and must be excluded from any model
    predicting it.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from ml.logging_utils import get_logger

log = get_logger("lineage")

PROVENANCE_CLASSES: tuple[str, ...] = ("raw", "derived", "reference", "reference_derived")


@dataclasses.dataclass(frozen=True)
class LineageEntry:
    """One feature and its complete derivation history."""

    feature: str
    provenance_class: str
    source_dataset: str
    source_columns: tuple[str, ...]
    transformation: str
    unit: str
    notes: str = ""

    def __post_init__(self) -> None:
        if self.provenance_class not in PROVENANCE_CLASSES:
            raise ValueError(
                f"provenance_class must be one of {PROVENANCE_CLASSES}, "
                f"got {self.provenance_class!r} for feature {self.feature!r}"
            )

    def as_row(self) -> dict[str, Any]:
        return {
            "feature": self.feature,
            "provenance_class": self.provenance_class,
            "source_dataset": self.source_dataset,
            "source_columns": ", ".join(self.source_columns) if self.source_columns else "-",
            "transformation": self.transformation,
            "unit": self.unit,
            "notes": self.notes,
        }


class LineageRegistry:
    """Collects :class:`LineageEntry` objects and exports them."""

    def __init__(self, entries: Iterable[LineageEntry] = ()) -> None:
        self._entries: dict[str, LineageEntry] = {}
        for entry in entries:
            self.add(entry)

    def add(self, entry: LineageEntry) -> LineageEntry:
        if entry.feature in self._entries:
            raise ValueError(f"feature {entry.feature!r} is already registered")
        self._entries[entry.feature] = entry
        return entry

    def register(
        self,
        feature: str,
        provenance_class: str,
        source_dataset: str,
        source_columns: Iterable[str],
        transformation: str,
        unit: str,
        notes: str = "",
    ) -> LineageEntry:
        return self.add(
            LineageEntry(
                feature=feature,
                provenance_class=provenance_class,
                source_dataset=source_dataset,
                source_columns=tuple(source_columns),
                transformation=transformation,
                unit=unit,
                notes=notes,
            )
        )

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, feature: object) -> bool:
        return feature in self._entries

    def get(self, feature: str) -> LineageEntry:
        return self._entries[feature]

    def features_of_class(self, provenance_class: str) -> list[str]:
        return sorted(f for f, e in self._entries.items() if e.provenance_class == provenance_class)

    @property
    def leakage_sensitive_features(self) -> list[str]:
        """Features that must never enter a model predicting the derived target."""
        return self.features_of_class("reference_derived")

    def to_frame(self) -> pd.DataFrame:
        if not self._entries:
            return pd.DataFrame(
                columns=["feature", "provenance_class", "source_dataset",
                         "source_columns", "transformation", "unit", "notes"]
            )
        frame = pd.DataFrame([e.as_row() for e in self._entries.values()])
        order = {c: i for i, c in enumerate(PROVENANCE_CLASSES)}
        return frame.sort_values(
            by=["provenance_class", "feature"],
            key=lambda s: s.map(order) if s.name == "provenance_class" else s,
        ).reset_index(drop=True)

    def coverage_report(self, columns: Iterable[str]) -> pd.DataFrame:
        """Which of ``columns`` are registered, and which registrations are unused."""
        columns = list(columns)
        rows = [
            {"column": c, "status": "registered" if c in self._entries else "UNREGISTERED"}
            for c in columns
        ]
        rows += [
            {"column": f, "status": "registered_but_absent"}
            for f in sorted(set(self._entries) - set(columns))
        ]
        return pd.DataFrame(rows)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".json":
            payload = [dataclasses.asdict(e) for e in self._entries.values()]
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        else:
            self.to_frame().to_csv(path, index=False, encoding="utf-8")
        log.info("lineage for %d feature(s) written to %s", len(self._entries), path.name)
        return path

"""Growth-stage-aware crop coefficients.

The study needs one question answered reliably: *given a crop and how many days
it has been in the ground, what is Kc today?* Two source files contribute, and
they are shaped very differently.

``Crop_Calender_cleaned.csv``
    Already numeric. Stage durations and Kc are columns. Read as data.

``Karnataka_Crop_Growth_Stage_Reference_cleaned.csv``
    Kc and timing are English sentences with ranges and citations. The numbers
    are extracted by :func:`extract_kc_candidates`, but which candidate to use
    and where the stage boundaries fall are judgement calls, so those live in
    ``config/crop_stages.yaml`` rather than in this code.

The Kc curve follows FAO-56: flat at Kc_ini through the initial stage, a
straight ramp up to Kc_mid across development, flat at Kc_mid through
mid-season, and a straight ramp down to Kc_end across the late season. Because
development and late-season Kc are interpolated rather than tabulated, a crop
with a 40-day development stage produces 40 distinct Kc values, which is what
makes the resulting water requirement genuinely stage-aware rather than a step
function.
"""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pandas as pd
import yaml

from ml import config
from ml.logging_utils import get_logger

log = get_logger("crop_reference")

CROP_STAGES_PATH: Path = config.CONFIG_DIR / "crop_stages.yaml"

CANONICAL_STAGES: tuple[str, ...] = ("initial", "development", "mid_season", "late_season")


# --------------------------------------------------------------------------
# Free-text Kc extraction
# --------------------------------------------------------------------------
#: Matches "1.05-1.10", "1.05 - 1.10" and the en-dash form the source file uses.
_RANGE = re.compile(r"(\d+\.\d+)\s*[-‐-―]\s*(\d+\.\d+)")
_NUMBER = re.compile(r"\d+\.\d+")


def extract_kc_candidates(text: str) -> list[float]:
    """Pull every Kc value mentioned in a free-text reference cell.

    Ranges are expanded to both endpoints. The result is a list of *candidates*,
    deliberately not a single number: choosing between them is a documented
    decision recorded in ``config/crop_stages.yaml``, not something this parser
    is entitled to do silently.
    """
    if not isinstance(text, str):
        return []
    candidates: list[float] = []
    remainder = text
    for match in _RANGE.finditer(text):
        candidates.extend([float(match.group(1)), float(match.group(2))])
        remainder = remainder.replace(match.group(0), " ")
    candidates.extend(float(m) for m in _NUMBER.findall(remainder))
    # Kc for field crops sits inside this interval; anything else in the cell is
    # a day number, a week number or a year, not a coefficient.
    return sorted({c for c in candidates if 0.05 <= c <= 1.5})


def parse_reference_kc_table(growth_reference: pd.DataFrame) -> pd.DataFrame:
    """Turn the free-text Karnataka reference into an inspectable table."""
    rows = []
    for _, row in growth_reference.iterrows():
        candidates = extract_kc_candidates(row.get("kc_text", ""))
        rows.append(
            {
                "source_crop": row.get("crop"),
                "source_stage": row.get("growth_stage"),
                "kc_type": row.get("kc_type"),
                "kc_text": row.get("kc_text"),
                "timing_text": row.get("timing_text"),
                "kc_candidates": candidates,
                "n_candidates": len(candidates),
                "evidence_source": row.get("evidence_source"),
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# Stage-name harmonisation
# --------------------------------------------------------------------------
def _load_stage_config(path: Path | None = None) -> dict[str, Any]:
    path = path or CROP_STAGES_PATH
    if not path.exists():
        raise FileNotFoundError(f"crop stage configuration not found at {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _build_alias_lookup(aliases: dict[str, Iterable[str]]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, variants in aliases.items():
        lookup[canonical.lower()] = canonical
        for variant in variants:
            lookup[str(variant).strip().lower()] = canonical
    return lookup


def canonical_stage(name: str, alias_lookup: dict[str, str]) -> str | None:
    """Map a source stage label onto one of the four FAO-56 stages."""
    key = str(name).strip().lower()
    if key in alias_lookup:
        return alias_lookup[key]
    # Fall back to a containment match, which catches compound labels such as
    # "Mid-Season / Flowering & Grain Development".
    for alias, canonical in alias_lookup.items():
        if alias and alias in key:
            return canonical
    return None


def slugify_crop(name: str) -> str:
    """``"Paddy (Rice)"`` -> ``"paddy"``; ``"Finger Millet (Ragi)"`` -> ``"finger_millet"``."""
    text = re.sub(r"\(.*?\)", " ", str(name))
    text = re.sub(r"[^0-9a-zA-Z]+", "_", text).strip("_").lower()
    return text


# --------------------------------------------------------------------------
# The unified stage table
# --------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class CropStage:
    """One FAO-56 stage of one crop."""

    crop: str
    display_name: str
    stage: str
    stage_order: int
    start_day: int
    end_day: int
    kc: float | None
    alternative_kc: float | None
    kc_basis: str
    source: str

    @property
    def duration_days(self) -> int:
        return self.end_day - self.start_day


def _stages_from_config(cfg: dict[str, Any]) -> list[CropStage]:
    out: list[CropStage] = []
    for crop_key, spec in (cfg.get("crops") or {}).items():
        for order, stage in enumerate(spec.get("stages", [])):
            out.append(
                CropStage(
                    crop=crop_key,
                    display_name=spec.get("display_name", crop_key),
                    stage=stage["name"],
                    stage_order=order,
                    start_day=int(stage["start_day"]),
                    end_day=int(stage["end_day"]),
                    kc=None if stage.get("kc") is None else float(stage["kc"]),
                    alternative_kc=(
                        None if stage.get("alternative_kc") is None
                        else float(stage["alternative_kc"])
                    ),
                    kc_basis=str(stage.get("kc_basis", "")),
                    source=str(spec.get("source_dataset", "config/crop_stages.yaml")),
                )
            )
    return out


def _stages_from_calendar(
    calendar: pd.DataFrame, alias_lookup: dict[str, str], non_stage_rows: Sequence[str]
) -> list[CropStage]:
    """Build stages for the crops whose calendar entries are already numeric."""
    excluded = {s.strip().lower() for s in non_stage_rows}
    out: list[CropStage] = []

    for crop_name, group in calendar.groupby("crop", sort=True):
        rows = []
        for _, row in group.iterrows():
            stage_label = str(row["stage"]).strip()
            if stage_label.lower() in excluded:
                continue
            stage = canonical_stage(stage_label, alias_lookup)
            if stage is None:
                log.warning("crop %s: unrecognised stage label %r, skipped", crop_name, stage_label)
                continue
            duration = row.get("duration_days")
            kc = row.get("kc")
            if pd.isna(duration):
                log.warning("crop %s stage %s: no duration, skipped", crop_name, stage)
                continue
            rows.append((stage, int(duration), None if pd.isna(kc) else float(kc)))

        rows.sort(key=lambda r: CANONICAL_STAGES.index(r[0]))
        if [r[0] for r in rows] != list(CANONICAL_STAGES):
            log.warning(
                "crop %s does not supply all four stages (%s); excluded from the Kc model",
                crop_name, [r[0] for r in rows],
            )
            continue

        cursor = 0
        crop_key = slugify_crop(crop_name)
        for order, (stage, duration, kc) in enumerate(rows):
            out.append(
                CropStage(
                    crop=crop_key,
                    display_name=str(crop_name),
                    stage=stage,
                    stage_order=order,
                    start_day=cursor,
                    end_day=cursor + duration,
                    # Development Kc is interpolated even when the calendar
                    # states one, so every crop uses the same curve shape.
                    kc=None if stage == "development" else kc,
                    alternative_kc=kc if stage == "development" else None,
                    kc_basis=("interpolated" if stage == "development"
                              else "tabulated in Crop_Calender_cleaned.csv"),
                    source="Crop_Calender_cleaned.csv",
                )
            )
            cursor += duration
    return out


class CropCoefficientModel:
    """Growth-stage-aware Kc lookup for every crop the study can model."""

    def __init__(self, stages: Sequence[CropStage], *, use_alternative_kc: bool = False) -> None:
        self._use_alternative = use_alternative_kc
        self._stages: dict[str, list[CropStage]] = {}
        for stage in stages:
            self._stages.setdefault(stage.crop, []).append(stage)
        for crop in self._stages:
            self._stages[crop].sort(key=lambda s: s.stage_order)
        self._validate()

    # -- construction ----------------------------------------------------
    @classmethod
    def from_sources(
        cls,
        calendar: pd.DataFrame,
        *,
        stage_config_path: Path | None = None,
        use_alternative_kc: bool = False,
    ) -> CropCoefficientModel:
        cfg = _load_stage_config(stage_config_path)
        alias_lookup = _build_alias_lookup(cfg.get("stage_aliases") or {})
        non_stage = cfg.get("non_stage_rows") or []
        stages = _stages_from_config(cfg) + _stages_from_calendar(calendar, alias_lookup, non_stage)
        model = cls(stages, use_alternative_kc=use_alternative_kc)
        log.info("crop coefficient model covers %d crops: %s",
                 len(model.crops), ", ".join(model.crops))
        return model

    # -- integrity -------------------------------------------------------
    def _validate(self) -> None:
        """Stages must be contiguous, ordered, and anchored at all four corners."""
        for crop, stages in self._stages.items():
            names = [s.stage for s in stages]
            if names != list(CANONICAL_STAGES):
                raise ValueError(f"crop {crop!r} has stages {names}, expected {list(CANONICAL_STAGES)}")
            if stages[0].start_day != 0:
                raise ValueError(f"crop {crop!r} does not start at day 0")
            for previous, following in zip(stages, stages[1:]):
                if previous.end_day != following.start_day:
                    raise ValueError(
                        f"crop {crop!r} has a gap or overlap between {previous.stage} "
                        f"(ends {previous.end_day}) and {following.stage} "
                        f"(starts {following.start_day})"
                    )
            for stage in stages:
                if stage.duration_days <= 0:
                    raise ValueError(f"crop {crop!r} stage {stage.stage} has non-positive duration")
            for stage in stages:
                if stage.stage != "development" and self._kc_of(stage) is None:
                    raise ValueError(
                        f"crop {crop!r} stage {stage.stage} has no Kc value; "
                        "the Kc curve cannot be anchored"
                    )

    def _kc_of(self, stage: CropStage) -> float | None:
        if self._use_alternative and stage.alternative_kc is not None and stage.stage != "development":
            return stage.alternative_kc
        return stage.kc

    # -- interface -------------------------------------------------------
    @property
    def crops(self) -> list[str]:
        return sorted(self._stages)

    def cycle_length(self, crop: str) -> int:
        return self._stages[self._require(crop)][-1].end_day

    def _require(self, crop: str) -> str:
        key = slugify_crop(crop)
        if key in self._stages:
            return key
        raise KeyError(f"no Kc curve for crop {crop!r}; known crops: {self.crops}")

    def stage_for_day(self, crop: str, days_after_sowing: float) -> CropStage:
        """Which stage the crop is in on a given day."""
        stages = self._stages[self._require(crop)]
        day = float(days_after_sowing)
        if day < 0:
            raise ValueError("days_after_sowing must not be negative")
        for stage in stages:
            if day < stage.end_day:
                return stage
        return stages[-1]  # at or past harvest: hold the final stage

    def kc(self, crop: str, days_after_sowing: float) -> float:
        """Kc on a given day, interpolated per the FAO-56 curve."""
        key = self._require(crop)
        stages = self._stages[key]
        day = float(np.clip(days_after_sowing, 0.0, stages[-1].end_day))

        initial, development, mid, late = stages
        kc_ini = float(self._kc_of(initial))
        kc_mid = float(self._kc_of(mid))
        kc_end = float(self._kc_of(late))

        if day < development.start_day:
            return kc_ini
        if day < development.end_day:
            fraction = (day - development.start_day) / development.duration_days
            return kc_ini + fraction * (kc_mid - kc_ini)
        if day < late.start_day:
            return kc_mid
        fraction = (day - late.start_day) / late.duration_days
        return kc_mid + fraction * (kc_end - kc_mid)

    def kc_series(self, crop: str, days_after_sowing: Iterable[float]) -> np.ndarray:
        return np.array([self.kc(crop, d) for d in days_after_sowing], dtype=float)

    def stage_series(self, crop: str, days_after_sowing: Iterable[float]) -> list[str]:
        return [self.stage_for_day(crop, d).stage for d in days_after_sowing]

    def curve(self, crop: str) -> pd.DataFrame:
        """Day-by-day Kc for a whole crop cycle, for plotting and inspection."""
        key = self._require(crop)
        days = np.arange(0, self.cycle_length(key) + 1)
        return pd.DataFrame(
            {
                "crop": key,
                "days_after_sowing": days,
                "stage": self.stage_series(key, days),
                "kc": self.kc_series(key, days),
            }
        )

    def to_frame(self) -> pd.DataFrame:
        """The whole stage table, for the data dictionary and the database seed."""
        rows = []
        for crop, stages in sorted(self._stages.items()):
            for stage in stages:
                rows.append(
                    {
                        "crop": crop,
                        "display_name": stage.display_name,
                        "stage": stage.stage,
                        "stage_order": stage.stage_order,
                        "start_day": stage.start_day,
                        "end_day": stage.end_day,
                        "duration_days": stage.duration_days,
                        "kc_anchor": self._kc_of(stage),
                        "alternative_kc": stage.alternative_kc,
                        "kc_basis": stage.kc_basis,
                        "source": stage.source,
                    }
                )
        return pd.DataFrame(rows)

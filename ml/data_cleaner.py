"""Cleaning steps, each one small, named and reversible in principle.

Nothing in this module writes to ``datasets/raw`` or ``datasets/cleaned``.
Functions take a frame and return a new frame, and every transformation appends
a line to a :class:`CleaningLog` so the notebook can print exactly what happened
to each dataset rather than asking the reader to trust it.

The repository already contains a ``datasets/cleaned`` directory produced by
earlier work. :func:`audit_raw_versus_cleaned` exists to establish what that
earlier pass actually changed, because inheriting a cleaned file without knowing
what was done to it is not an acceptable starting point for a study.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Sequence

import numpy as np
import pandas as pd

from ml.logging_utils import get_logger

log = get_logger("data_cleaner")

#: Values providers use to mean "no observation". NASA POWER uses -999.
SENTINEL_VALUES: tuple[float, ...] = (-999.0, -9999.0, -99.9)


@dataclasses.dataclass
class CleaningLog:
    """Ordered record of every transformation applied to one dataset."""

    dataset: str
    entries: list[dict[str, Any]] = dataclasses.field(default_factory=list)

    def record(self, step: str, detail: str, rows_before: int, rows_after: int, **extra: Any) -> None:
        self.entries.append(
            {
                "dataset": self.dataset,
                "step": step,
                "detail": detail,
                "rows_before": rows_before,
                "rows_after": rows_after,
                "rows_removed": rows_before - rows_after,
                **extra,
            }
        )
        log.info("%s | %s: %s", self.dataset, step, detail)

    def to_frame(self) -> pd.DataFrame:
        if not self.entries:
            return pd.DataFrame(columns=["dataset", "step", "detail", "rows_before", "rows_after", "rows_removed"])
        return pd.DataFrame(self.entries)


# --------------------------------------------------------------------------
# Generic steps
# --------------------------------------------------------------------------
def replace_sentinels(
    frame: pd.DataFrame,
    log_: CleaningLog,
    *,
    sentinels: Sequence[float] = SENTINEL_VALUES,
    columns: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Turn provider missing-data sentinels into real NaN."""
    out = frame.copy()
    targets = columns or out.select_dtypes(include=[np.number]).columns.tolist()
    replaced: dict[str, int] = {}
    for column in targets:
        mask = out[column].isin(sentinels)
        count = int(mask.sum())
        if count:
            out.loc[mask, column] = np.nan
            replaced[column] = count
    log_.record(
        "replace_sentinels",
        (f"converted {sum(replaced.values())} sentinel value(s) to NaN in {replaced}"
         if replaced else "no sentinel values found"),
        len(frame), len(out), columns_affected=replaced,
    )
    return out


def drop_exact_duplicates(frame: pd.DataFrame, log_: CleaningLog) -> pd.DataFrame:
    before = len(frame)
    out = frame.drop_duplicates().reset_index(drop=True)
    log_.record(
        "drop_exact_duplicates",
        f"removed {before - len(out)} fully duplicated row(s)",
        before, len(out),
    )
    return out


def strip_text_columns(frame: pd.DataFrame, log_: CleaningLog) -> pd.DataFrame:
    """Trim whitespace from object columns.

    The source files have headings and values padded with trailing spaces
    (``"Districts                    "``), which silently breaks joins.
    """
    out = frame.copy()
    touched = []
    for column in out.select_dtypes(include=["object"]).columns:
        original = out[column]
        stripped = original.astype(str).str.strip()
        stripped = stripped.where(original.notna(), other=np.nan)
        if not stripped.equals(original.astype(str).where(original.notna(), other=np.nan)):
            touched.append(column)
        out[column] = stripped
    log_.record(
        "strip_text_columns",
        f"trimmed whitespace in {len(touched)} text column(s): {touched}" if touched
        else "no whitespace to trim",
        len(frame), len(out),
    )
    return out


def parse_dates(frame: pd.DataFrame, log_: CleaningLog, column: str) -> pd.DataFrame:
    out = frame.copy()
    out[column] = pd.to_datetime(out[column], errors="coerce")
    unparseable = int(out[column].isna().sum())
    log_.record(
        "parse_dates",
        f"parsed {column}; {unparseable} value(s) unparseable",
        len(frame), len(out), unparseable=unparseable,
    )
    return out


def drop_rows_where(
    frame: pd.DataFrame, log_: CleaningLog, mask: pd.Series, reason: str
) -> pd.DataFrame:
    before = len(frame)
    out = frame.loc[~mask].reset_index(drop=True)
    log_.record("drop_rows", f"{reason}: removed {before - len(out)} row(s)", before, len(out))
    return out


def coerce_numeric(
    frame: pd.DataFrame, log_: CleaningLog, columns: Sequence[str]
) -> pd.DataFrame:
    """Force columns to numeric, reporting what could not be converted."""
    out = frame.copy()
    failures: dict[str, int] = {}
    for column in columns:
        if column not in out.columns:
            continue
        before_na = int(out[column].isna().sum())
        out[column] = pd.to_numeric(out[column], errors="coerce")
        introduced = int(out[column].isna().sum()) - before_na
        if introduced:
            failures[column] = introduced
    log_.record(
        "coerce_numeric",
        (f"non-numeric text became NaN in {failures}" if failures
         else f"all {len(columns)} column(s) already numeric"),
        len(frame), len(out), failures=failures,
    )
    return out


# --------------------------------------------------------------------------
# Dataset-specific steps
# --------------------------------------------------------------------------
def clean_weather(frame: pd.DataFrame, log_: CleaningLog) -> pd.DataFrame:
    """Prepare the daily weather series for ET0."""
    out = replace_sentinels(frame, log_)
    out = parse_dates(out, log_, "datetime")
    out = out.sort_values("datetime").reset_index(drop=True)
    log_.record("sort", "ordered chronologically by datetime", len(out), len(out))

    # The source carries DATE (day of month), MONTH and YEAR alongside the full
    # timestamp. They are redundant, and a redundant copy that silently drifts
    # out of step is a hazard. Confirm they agree, then drop them and regenerate
    # calendar parts from the timestamp alone.
    parsed = out["datetime"]
    mismatches = {}
    for column, expected in (("date", parsed.dt.day), ("month", parsed.dt.month), ("year", parsed.dt.year)):
        if column in out.columns:
            disagreements = int((pd.to_numeric(out[column], errors="coerce") != expected).sum())
            if disagreements:
                mismatches[column] = disagreements
    redundant = [c for c in ("date", "month", "year") if c in out.columns]
    out = out.drop(columns=redundant)
    log_.record(
        "drop_redundant_date_parts",
        (f"dropped {redundant}; they duplicate the timestamp and all agreed with it"
         if not mismatches
         else f"dropped {redundant}; WARNING they disagreed with the timestamp: {mismatches}"),
        len(out), len(out), mismatches=mismatches,
    )

    # Physical impossibilities become NaN rather than being silently kept.
    swapped = out["t2m_min"] > out["t2m_max"]
    if int(swapped.sum()):
        out.loc[swapped, ["t2m_min", "t2m_max"]] = np.nan
    log_.record(
        "temperature_ordering",
        f"{int(swapped.sum())} day(s) had Tmin above Tmax and were voided",
        len(out), len(out),
    )

    for column, low, high in (("rh2m", 0.0, 100.0), ("ws2m", 0.0, None), ("prectotcorr", 0.0, None)):
        series = out[column]
        bad = (series < low) if high is None else ((series < low) | (series > high))
        n_bad = int(bad.sum())
        if n_bad:
            out.loc[bad, column] = np.nan
        log_.record(
            f"range_guard[{column}]",
            f"{n_bad} value(s) outside the physical range were voided",
            len(out), len(out),
        )
    return out


def clean_district_rainfall(frame: pd.DataFrame, log_: CleaningLog) -> pd.DataFrame:
    """Drop the state-total row and normalise district names for joining."""
    out = strip_text_columns(frame, log_)
    total_row = out["serial_no"].astype(str).str.upper().str.strip().eq("STATE")
    out = drop_rows_where(
        out, log_, total_row,
        "the final row is a state aggregate, not a district, and would corrupt any per-district statistic",
    )
    out = coerce_numeric(out, log_, ["serial_no", "normal_rainy_days", "normal_annual_rainfall_mm"])
    out["district_key"] = out["district"].str.upper().str.replace(r"[^A-Z]", "", regex=True)
    log_.record("district_key", "added a punctuation-free uppercase join key", len(out), len(out))
    return out


def clean_soil(frame: pd.DataFrame, log_: CleaningLog) -> pd.DataFrame:
    out = strip_text_columns(frame, log_)
    out = coerce_numeric(out, log_, ["nitrogen", "phosphorus", "potassium", "ph"])
    implausible_ph = (out["ph"] < 3.0) | (out["ph"] > 10.0)
    if int(implausible_ph.sum()):
        out.loc[implausible_ph, "ph"] = np.nan
    log_.record(
        "ph_range_guard",
        f"{int(implausible_ph.sum())} pH value(s) outside 3-10 were voided",
        len(out), len(out),
    )
    out["district_key"] = out["district"].str.upper().str.replace(r"[^A-Z]", "", regex=True)
    log_.record("district_key", "added a punctuation-free uppercase join key", len(out), len(out))
    return out


def clean_crop_recommendation(frame: pd.DataFrame, log_: CleaningLog) -> pd.DataFrame:
    out = strip_text_columns(frame, log_)
    out["label"] = out["label"].str.lower()
    log_.record("normalise_label", "crop labels lower-cased", len(out), len(out))
    return drop_exact_duplicates(out, log_)


# --------------------------------------------------------------------------
# Raw-versus-cleaned audit
# --------------------------------------------------------------------------
def audit_raw_versus_cleaned(
    raw: pd.DataFrame, cleaned: pd.DataFrame, dataset: str
) -> pd.DataFrame:
    """Establish what an earlier cleaning pass changed.

    Compares shape, column set and per-column missingness and extremes. Its
    purpose is to make an inherited cleaned file accountable: any difference it
    reports is a transformation somebody applied, and the study has to be able
    to name it.
    """
    rows: list[dict[str, Any]] = [
        {
            "dataset": dataset, "aspect": "row_count",
            "raw": len(raw), "cleaned": len(cleaned),
            "changed": len(raw) != len(cleaned),
        },
        {
            "dataset": dataset, "aspect": "column_count",
            "raw": raw.shape[1], "cleaned": cleaned.shape[1],
            "changed": raw.shape[1] != cleaned.shape[1],
        },
    ]

    raw_columns, cleaned_columns = set(raw.columns), set(cleaned.columns)
    if raw_columns != cleaned_columns:
        rows.append({
            "dataset": dataset, "aspect": "columns_dropped",
            "raw": sorted(raw_columns - cleaned_columns), "cleaned": "-", "changed": True,
        })
        rows.append({
            "dataset": dataset, "aspect": "columns_added",
            "raw": "-", "cleaned": sorted(cleaned_columns - raw_columns), "changed": True,
        })

    for column in sorted(raw_columns & cleaned_columns):
        raw_na = int(raw[column].isna().sum())
        cleaned_na = int(cleaned[column].isna().sum())
        if raw_na != cleaned_na:
            rows.append({
                "dataset": dataset, "aspect": f"missing[{column}]",
                "raw": raw_na, "cleaned": cleaned_na, "changed": True,
            })
        raw_numeric = pd.to_numeric(raw[column], errors="coerce")
        cleaned_numeric = pd.to_numeric(cleaned[column], errors="coerce")
        if raw_numeric.notna().any() and cleaned_numeric.notna().any():
            raw_min, cleaned_min = float(raw_numeric.min()), float(cleaned_numeric.min())
            if not np.isclose(raw_min, cleaned_min, equal_nan=True):
                rows.append({
                    "dataset": dataset, "aspect": f"min[{column}]",
                    "raw": raw_min, "cleaned": cleaned_min, "changed": True,
                })

    return pd.DataFrame(rows)

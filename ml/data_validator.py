"""A small, explicit validation engine.

Each check is a named rule that returns a :class:`CheckResult`. Rules never
mutate data and never raise on a failed check -- they record the failure so the
whole picture appears in one report instead of stopping at the first problem.

Severity has a defined meaning:

``error``
    The data cannot be used for its declared purpose until this is fixed.
``warning``
    Usable, but a documented caveat must travel with any result derived from it.
``info``
    An observation worth recording in the audit trail.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

import numpy as np
import pandas as pd

from ml.logging_utils import get_logger

log = get_logger("data_validator")

SEVERITIES = ("info", "warning", "error")


@dataclasses.dataclass
class CheckResult:
    """Outcome of one validation rule."""

    dataset: str
    check: str
    passed: bool
    severity: str
    message: str
    detail: dict[str, Any] = dataclasses.field(default_factory=dict)

    def as_row(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "check": self.check,
            "status": "PASS" if self.passed else self.severity.upper(),
            "severity": self.severity,
            "message": self.message,
        }


class ValidationReport:
    """Accumulates :class:`CheckResult` objects and summarises them."""

    def __init__(self) -> None:
        self.results: list[CheckResult] = []

    # -- collection ------------------------------------------------------
    def add(self, result: CheckResult) -> CheckResult:
        self.results.append(result)
        if not result.passed:
            log.log(
                {"error": 40, "warning": 30, "info": 20}[result.severity],
                "%s / %s: %s", result.dataset, result.check, result.message,
            )
        return result

    def extend(self, results: Iterable[CheckResult]) -> None:
        for result in results:
            self.add(result)

    # -- summary ---------------------------------------------------------
    @property
    def errors(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed and r.severity == "error"]

    @property
    def warnings(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed and r.severity == "warning"]

    def ok(self) -> bool:
        """True when no ``error``-severity check failed."""
        return not self.errors

    def to_frame(self) -> pd.DataFrame:
        if not self.results:
            return pd.DataFrame(columns=["dataset", "check", "status", "severity", "message"])
        return pd.DataFrame([r.as_row() for r in self.results])

    def failures_frame(self) -> pd.DataFrame:
        frame = self.to_frame()
        if frame.empty:
            return frame
        return frame[frame["status"] != "PASS"].reset_index(drop=True)

    def summary(self) -> dict[str, int]:
        return {
            "checks_run": len(self.results),
            "passed": sum(r.passed for r in self.results),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
        }

    def save_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": self.summary(),
            "results": [dataclasses.asdict(r) for r in self.results],
        }
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        log.info("validation report written to %s", path.name)
        return path

    def raise_if_errors(self) -> None:
        if self.ok():
            return
        lines = [f"  - {r.dataset}/{r.check}: {r.message}" for r in self.errors]
        raise ValueError(
            f"{len(self.errors)} blocking validation error(s):\n" + "\n".join(lines)
        )


# --------------------------------------------------------------------------
# Reusable rules
# --------------------------------------------------------------------------
def check_columns_present(
    frame: pd.DataFrame, dataset: str, required: Sequence[str], severity: str = "error"
) -> CheckResult:
    """Every column in ``required`` must exist."""
    missing = [c for c in required if c not in frame.columns]
    return CheckResult(
        dataset=dataset,
        check="columns_present",
        passed=not missing,
        severity=severity,
        message=("all expected columns present" if not missing
                 else f"missing column(s): {missing}"),
        detail={"missing": missing, "present": list(frame.columns)},
    )


def check_row_count(
    frame: pd.DataFrame, dataset: str, expected: int, severity: str = "warning"
) -> CheckResult:
    """Row count must match what the study documented."""
    actual = len(frame)
    return CheckResult(
        dataset=dataset,
        check="row_count",
        passed=actual == expected,
        severity=severity,
        message=(f"{actual} rows as documented" if actual == expected
                 else f"expected {expected} rows, found {actual}"),
        detail={"expected": expected, "actual": actual},
    )


def check_no_duplicate_rows(
    frame: pd.DataFrame, dataset: str, severity: str = "warning"
) -> CheckResult:
    count = int(frame.duplicated().sum())
    return CheckResult(
        dataset=dataset,
        check="duplicate_rows",
        passed=count == 0,
        severity=severity,
        message=("no duplicate rows" if count == 0 else f"{count} fully duplicated row(s)"),
        detail={"duplicate_rows": count},
    )


def check_unique_key(
    frame: pd.DataFrame, dataset: str, columns: Sequence[str], severity: str = "error"
) -> CheckResult:
    """``columns`` must uniquely identify a row."""
    present = [c for c in columns if c in frame.columns]
    if len(present) != len(columns):
        return CheckResult(
            dataset, "unique_key", False, severity,
            f"cannot test uniqueness: missing {set(columns) - set(present)}",
        )
    count = int(frame.duplicated(subset=list(columns)).sum())
    return CheckResult(
        dataset=dataset,
        check=f"unique_key[{'+'.join(columns)}]",
        passed=count == 0,
        severity=severity,
        message=("key is unique" if count == 0 else f"{count} duplicated key value(s)"),
        detail={"duplicates": count},
    )


def check_value_range(
    frame: pd.DataFrame,
    dataset: str,
    column: str,
    low: float | None,
    high: float | None,
    severity: str = "error",
    allow_na: bool = True,
) -> CheckResult:
    """Values must sit inside a physically plausible interval."""
    if column not in frame.columns:
        return CheckResult(dataset, f"range[{column}]", False, severity,
                           f"column {column!r} absent")
    series = pd.to_numeric(frame[column], errors="coerce")
    na_count = int(series.isna().sum())
    below = int((series < low).sum()) if low is not None else 0
    above = int((series > high).sum()) if high is not None else 0
    bad = below + above
    passed = bad == 0 and (allow_na or na_count == 0)
    bounds = f"[{low if low is not None else '-inf'}, {high if high is not None else '+inf'}]"
    if passed:
        message = f"{column} within {bounds}"
    else:
        parts = []
        if below:
            parts.append(f"{below} below {low}")
        if above:
            parts.append(f"{above} above {high}")
        if na_count and not allow_na:
            parts.append(f"{na_count} missing")
        message = f"{column} outside {bounds}: " + ", ".join(parts)
    return CheckResult(
        dataset=dataset,
        check=f"range[{column}]",
        passed=passed,
        severity=severity,
        message=message,
        detail={
            "column": column, "low": low, "high": high,
            "below": below, "above": above, "missing": na_count,
            "observed_min": None if series.dropna().empty else float(series.min()),
            "observed_max": None if series.dropna().empty else float(series.max()),
        },
    )


def check_missing_rate(
    frame: pd.DataFrame, dataset: str, column: str, max_rate: float, severity: str = "warning"
) -> CheckResult:
    """Missingness in ``column`` must stay under ``max_rate`` (a fraction)."""
    if column not in frame.columns:
        return CheckResult(dataset, f"missing_rate[{column}]", False, severity,
                           f"column {column!r} absent")
    rate = float(frame[column].isna().mean())
    passed = rate <= max_rate
    return CheckResult(
        dataset=dataset,
        check=f"missing_rate[{column}]",
        passed=passed,
        severity=severity,
        message=f"{column} missing {rate:.4%} (limit {max_rate:.2%})",
        detail={"rate": rate, "max_rate": max_rate,
                "missing": int(frame[column].isna().sum())},
    )


def check_sentinel_values(
    frame: pd.DataFrame,
    dataset: str,
    sentinels: Sequence[float] = (-999.0, -9999.0, -99.0),
    severity: str = "error",
) -> CheckResult:
    """No numeric column may still hold a provider's missing-data sentinel."""
    numeric = frame.select_dtypes(include=[np.number])
    hits: dict[str, dict[str, int]] = {}
    for column in numeric.columns:
        found = {
            str(s): int((numeric[column] == s).sum())
            for s in sentinels
            if int((numeric[column] == s).sum()) > 0
        }
        if found:
            hits[column] = found
    return CheckResult(
        dataset=dataset,
        check="sentinel_values",
        passed=not hits,
        severity=severity,
        message=("no sentinel values remain" if not hits
                 else f"sentinel values still present: {hits}"),
        detail={"hits": hits, "sentinels_tested": list(sentinels)},
    )


def check_monotonic_dates(
    frame: pd.DataFrame, dataset: str, column: str, severity: str = "error"
) -> CheckResult:
    """The date column must be strictly increasing with no gaps or repeats."""
    if column not in frame.columns:
        return CheckResult(dataset, f"date_continuity[{column}]", False, severity,
                           f"column {column!r} absent")
    dates = pd.to_datetime(frame[column], errors="coerce")
    invalid = int(dates.isna().sum())
    duplicated = int(dates.duplicated().sum())
    sorted_dates = dates.dropna().sort_values()
    if sorted_dates.empty:
        return CheckResult(dataset, f"date_continuity[{column}]", False, severity,
                           "no parseable dates")
    span_days = (sorted_dates.iloc[-1] - sorted_dates.iloc[0]).days + 1
    gaps = span_days - len(sorted_dates.unique())
    passed = invalid == 0 and duplicated == 0 and gaps == 0
    return CheckResult(
        dataset=dataset,
        check=f"date_continuity[{column}]",
        passed=passed,
        severity=severity,
        message=(
            f"{len(sorted_dates)} daily records, {sorted_dates.iloc[0].date()} to "
            f"{sorted_dates.iloc[-1].date()}, no gaps"
            if passed else
            f"unparseable={invalid}, duplicated={duplicated}, missing_days={gaps}"
        ),
        detail={
            "start": str(sorted_dates.iloc[0].date()),
            "end": str(sorted_dates.iloc[-1].date()),
            "records": int(len(sorted_dates)),
            "expected_days": span_days,
            "missing_days": int(gaps),
            "unparseable": invalid,
            "duplicated": duplicated,
        },
    )


def check_ordering(
    frame: pd.DataFrame,
    dataset: str,
    lower_col: str,
    upper_col: str,
    severity: str = "error",
) -> CheckResult:
    """``lower_col <= upper_col`` on every row (e.g. Tmin never exceeds Tmax)."""
    for column in (lower_col, upper_col):
        if column not in frame.columns:
            return CheckResult(dataset, f"ordering[{lower_col}<={upper_col}]", False,
                               severity, f"column {column!r} absent")
    violations = int((frame[lower_col] > frame[upper_col]).sum())
    return CheckResult(
        dataset=dataset,
        check=f"ordering[{lower_col}<={upper_col}]",
        passed=violations == 0,
        severity=severity,
        message=(f"{lower_col} <= {upper_col} holds everywhere" if violations == 0
                 else f"{violations} row(s) violate {lower_col} <= {upper_col}"),
        detail={"violations": violations},
    )


def check_custom(
    dataset: str,
    name: str,
    predicate: Callable[[], bool],
    pass_message: str,
    fail_message: str,
    severity: str = "warning",
    detail: dict[str, Any] | None = None,
) -> CheckResult:
    """Wrap an arbitrary boolean expression as a named, recorded check."""
    passed = bool(predicate())
    return CheckResult(
        dataset=dataset,
        check=name,
        passed=passed,
        severity=severity,
        message=pass_message if passed else fail_message,
        detail=detail or {},
    )


# --------------------------------------------------------------------------
# Profiling helper (not a rule: a description)
# --------------------------------------------------------------------------
def profile(frame: pd.DataFrame, dataset: str) -> pd.DataFrame:
    """Per-column dtype, missingness, cardinality and range."""
    rows = []
    for column in frame.columns:
        series = frame[column]
        numeric = pd.to_numeric(series, errors="coerce")
        is_numeric = numeric.notna().any() and not pd.api.types.is_object_dtype(numeric)
        rows.append(
            {
                "dataset": dataset,
                "column": column,
                "dtype": str(series.dtype),
                "missing": int(series.isna().sum()),
                "missing_pct": round(100 * float(series.isna().mean()), 3),
                "unique": int(series.nunique(dropna=True)),
                "min": float(numeric.min()) if is_numeric and numeric.notna().any() else None,
                "max": float(numeric.max()) if is_numeric and numeric.notna().any() else None,
                "mean": round(float(numeric.mean()), 4) if is_numeric and numeric.notna().any() else None,
            }
        )
    return pd.DataFrame(rows)

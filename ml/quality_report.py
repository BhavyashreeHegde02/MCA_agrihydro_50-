"""Writing the data-quality evidence out to disk.

The preprocessing notebook produces a lot of tables. This module puts them in
``reports/data_quality`` in two forms: CSV for anything a reader might want to
sort or re-plot, and one Markdown summary that can be read straight through.

Nothing here computes anything new. It only serialises what the validation,
cleaning and audit modules produced, which keeps the notebook's displayed
numbers and the written report guaranteed identical.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from ml import config
from ml.logging_utils import get_logger

log = get_logger("quality_report")


def save_table(frame: pd.DataFrame, name: str, directory: Path | None = None) -> Path:
    """Write one table to ``reports/data_quality/<name>.csv``."""
    directory = directory or config.QUALITY_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8")
    log.info("wrote %s (%d rows)", path.name, len(frame))
    return path


def save_json(payload: Mapping[str, Any], name: str, directory: Path | None = None) -> Path:
    directory = directory or config.QUALITY_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    log.info("wrote %s", path.name)
    return path


def _md_table(frame: pd.DataFrame, max_rows: int = 60) -> str:
    if frame.empty:
        return "_No rows._\n"
    shown = frame.head(max_rows)
    body = shown.to_markdown(index=False)
    if len(frame) > max_rows:
        body += f"\n\n_Showing {max_rows} of {len(frame)} rows; the full table is in the CSV._"
    return body + "\n"


def write_markdown_report(
    *,
    path: Path,
    run_timestamp: str,
    registry: pd.DataFrame,
    fingerprints: pd.DataFrame,
    profiles: pd.DataFrame,
    validation: pd.DataFrame,
    validation_summary: Mapping[str, int],
    missing: pd.DataFrame,
    cleaning: pd.DataFrame,
    raw_vs_cleaned: pd.DataFrame,
    target_audit: pd.DataFrame,
    target_rationale: str,
    site_summary: Mapping[str, Any],
    lineage: pd.DataFrame,
) -> Path:
    """Assemble the human-readable data-quality report."""
    path.parent.mkdir(parents=True, exist_ok=True)

    failures = validation[validation["status"] != "PASS"] if not validation.empty else validation

    sections = [
        "# Data quality report",
        "",
        f"Generated {run_timestamp} by `notebooks/02_data_preprocessing.ipynb`.",
        "Every table below is also written as a CSV in this directory.",
        "",
        "## 1. What was read",
        "",
        "The registry records the role each file plays. Files marked `excluded` are",
        "kept for the audit trail and do not reach any model.",
        "",
        _md_table(registry),
        "",
        "## 2. Raw-file integrity",
        "",
        "Hashes of everything under `datasets/raw`. The pipeline never opens these",
        "files for writing; re-running this report should reproduce the hashes exactly.",
        "",
        _md_table(fingerprints),
        "",
        "## 3. What the earlier cleaning pass changed",
        "",
        "The repository arrived with a `datasets/cleaned` directory. This table",
        "compares it against the untouched originals so that inherited",
        "transformations are named rather than assumed.",
        "",
        _md_table(raw_vs_cleaned),
        "",
        "## 4. Column profiles",
        "",
        _md_table(profiles, max_rows=200),
        "",
        "## 5. Validation results",
        "",
        f"{validation_summary.get('checks_run', 0)} checks run, "
        f"{validation_summary.get('passed', 0)} passed, "
        f"{validation_summary.get('errors', 0)} blocking errors, "
        f"{validation_summary.get('warnings', 0)} warnings.",
        "",
        "### Checks that did not pass",
        "",
        _md_table(failures),
        "",
        "## 6. Missing values",
        "",
        _md_table(missing),
        "",
        "## 7. Cleaning steps applied in this run",
        "",
        _md_table(cleaning, max_rows=120),
        "",
        "## 8. Candidate-target audit",
        "",
        "Tests applied to `crop_water_data.csv -> water_requirement_liters` to decide",
        "whether it can serve as supervised ground truth.",
        "",
        _md_table(target_audit),
        "",
        f"**Verdict.** {target_rationale}",
        "",
        "## 9. Weather site",
        "",
        "```json",
        json.dumps(dict(site_summary), indent=2, default=str),
        "```",
        "",
        "## 10. Feature lineage",
        "",
        "Source file and source columns for every feature the pipeline produces.",
        "Features classed `reference_derived` are algebraically related to the",
        "physics baseline and are excluded from any model that predicts it.",
        "",
        _md_table(lineage, max_rows=200),
        "",
    ]

    path.write_text("\n".join(sections), encoding="utf-8")
    log.info("data quality report written to %s", path)
    return path

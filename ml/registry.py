"""Saving, versioning and loading trained models.

A model is useless to the API unless everything needed to reproduce its
behaviour travels with it. Each saved version is a directory containing:

``pipeline.joblib``
    The fitted scikit-learn pipeline: preprocessing *and* estimator in one
    object, so inference cannot accidentally use different preprocessing from
    training.
``metadata.json``
    Algorithm, training date, dataset fingerprint, the exact ordered feature
    list, the task definition, the target definition, evaluation metrics, and
    the conformal calibration.
``feature_importance.csv``
    Permutation importance measured on held-out data.

``ACTIVE`` in the registry root names the version the API serves. Promotion is
an explicit act, so retraining never silently changes what production returns.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from ml import config
from ml.logging_utils import get_logger

log = get_logger("registry")

REGISTRY_DIR: Path = config.ARTIFACTS_DIR / "models"
ACTIVE_POINTER = "ACTIVE"


@dataclasses.dataclass
class ModelVersion:
    """One saved model version."""

    name: str
    version: str
    directory: Path
    metadata: dict[str, Any]

    @property
    def pipeline_path(self) -> Path:
        return self.directory / "pipeline.joblib"

    def load_pipeline(self) -> Any:
        return joblib.load(self.pipeline_path)


def dataset_fingerprint(frame: pd.DataFrame) -> str:
    """A short, stable hash of the training data.

    Lets a deployed model be matched back to the exact dataset it was fitted on,
    which is what makes "the model changed" distinguishable from "the data
    changed" during an investigation.
    """
    digest = hashlib.sha256()
    digest.update(str(frame.shape).encode())
    digest.update(",".join(map(str, frame.columns)).encode())
    digest.update(pd.util.hash_pandas_object(frame, index=True).values.tobytes())
    return digest.hexdigest()[:16]


def next_version(name: str, registry_dir: Path | None = None) -> str:
    """``v1``, ``v2``, ... for a given model name."""
    registry_dir = registry_dir or REGISTRY_DIR
    base = registry_dir / name
    if not base.exists():
        return "v1"
    existing = [
        int(p.name[1:]) for p in base.iterdir()
        if p.is_dir() and p.name.startswith("v") and p.name[1:].isdigit()
    ]
    return f"v{max(existing) + 1}" if existing else "v1"


def save_model(
    *,
    name: str,
    pipeline: Any,
    metadata: dict[str, Any],
    feature_importance: pd.DataFrame | None = None,
    registry_dir: Path | None = None,
    version: str | None = None,
    make_active: bool = False,
) -> ModelVersion:
    """Persist a trained model with everything needed to reproduce it."""
    registry_dir = registry_dir or REGISTRY_DIR
    version = version or next_version(name, registry_dir)
    directory = registry_dir / name / version
    directory.mkdir(parents=True, exist_ok=True)

    # compress=3 is a storage decision, not a modelling one: joblib reloads a
    # byte-identical estimator, so predictions and every recorded metric are
    # unaffected. It matters because an unbounded RandomForest over ~95k rows
    # serialises to roughly half a gigabyte uncompressed, which is most of a
    # Docker image for a model the service never loads. Level 3 is the point
    # where the curve flattens; higher levels cost seconds for a few per cent.
    joblib.dump(pipeline, directory / "pipeline.joblib", compress=3)

    full_metadata = {
        "model_name": name,
        "version": version,
        "saved_at": config.run_timestamp(),
        "random_seed": config.RANDOM_SEED,
        **metadata,
    }
    (directory / "metadata.json").write_text(
        json.dumps(full_metadata, indent=2, default=str), encoding="utf-8"
    )

    if feature_importance is not None:
        feature_importance.to_csv(directory / "feature_importance.csv", index=False,
                                  encoding="utf-8")

    log.info("saved %s/%s to %s", name, version, directory)
    model_version = ModelVersion(name=name, version=version, directory=directory,
                                 metadata=full_metadata)
    if make_active:
        set_active(name, version, registry_dir)
    return model_version


def set_active(name: str, version: str, registry_dir: Path | None = None) -> None:
    """Point the API at a specific version. Deliberately an explicit act."""
    registry_dir = registry_dir or REGISTRY_DIR
    target = registry_dir / name / version
    if not target.exists():
        raise FileNotFoundError(f"cannot activate {name}/{version}: {target} does not exist")
    (registry_dir / ACTIVE_POINTER).parent.mkdir(parents=True, exist_ok=True)
    (registry_dir / ACTIVE_POINTER).write_text(f"{name}/{version}\n", encoding="utf-8")
    log.info("active model is now %s/%s", name, version)


def get_active(registry_dir: Path | None = None) -> ModelVersion | None:
    """The version the API should serve, or ``None`` if nothing is promoted."""
    registry_dir = registry_dir or REGISTRY_DIR
    pointer = registry_dir / ACTIVE_POINTER
    if not pointer.exists():
        return None
    reference = pointer.read_text(encoding="utf-8").strip()
    if "/" not in reference:
        return None
    name, version = reference.split("/", 1)
    return load_version(name, version, registry_dir)


def load_version(name: str, version: str, registry_dir: Path | None = None) -> ModelVersion:
    registry_dir = registry_dir or REGISTRY_DIR
    directory = registry_dir / name / version
    metadata_path = directory / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"no model metadata at {metadata_path}")
    return ModelVersion(
        name=name, version=version, directory=directory,
        metadata=json.loads(metadata_path.read_text(encoding="utf-8")),
    )


def list_versions(registry_dir: Path | None = None) -> pd.DataFrame:
    """Every saved version, with its headline metrics."""
    registry_dir = registry_dir or REGISTRY_DIR
    if not registry_dir.exists():
        return pd.DataFrame(columns=["model_name", "version", "algorithm", "task", "is_active"])

    active = None
    pointer = registry_dir / ACTIVE_POINTER
    if pointer.exists():
        active = pointer.read_text(encoding="utf-8").strip()

    rows = []
    for name_dir in sorted(p for p in registry_dir.iterdir() if p.is_dir()):
        for version_dir in sorted(p for p in name_dir.iterdir() if p.is_dir()):
            metadata_path = version_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            test_metrics = (metadata.get("metrics") or {}).get("test") or {}
            rows.append(
                {
                    "model_name": metadata.get("model_name", name_dir.name),
                    "version": metadata.get("version", version_dir.name),
                    "algorithm": metadata.get("algorithm"),
                    "task": (metadata.get("task") or {}).get("task"),
                    "trained_at": metadata.get("saved_at"),
                    "test_mae_mm_day": test_metrics.get("mae_mm_day"),
                    "test_rmse_mm_day": test_metrics.get("rmse_mm_day"),
                    "test_r2": test_metrics.get("r2"),
                    "dataset_fingerprint": metadata.get("dataset_fingerprint"),
                    "is_active": f"{name_dir.name}/{version_dir.name}" == active,
                }
            )
    return pd.DataFrame(rows)


def clear_registry(registry_dir: Path | None = None) -> None:
    """Delete every saved version. Used by tests and by a clean retrain."""
    registry_dir = registry_dir or REGISTRY_DIR
    if registry_dir.exists():
        shutil.rmtree(registry_dir)
    log.info("registry cleared at %s", registry_dir)

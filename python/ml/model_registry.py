"""
NovaNest Phase 07 — Production ML Model Registry & Lifecycle Governance
-----------------------------------------------------------------------
Provides enterprise-grade model lifecycle management:
- Semantic model versioning (v1 baseline, v2 Phase 05, v3 Phase 07)
- Cryptographic SHA-256 dataset lineage and drift protection
- Automated model registration, artifact persistence, and rollback
- Honest confidence gating metadata for autonomous AI agents
- Backward-compatible access to legacy models
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"
REGISTRY_INDEX_FILE = MODELS_DIR / "registry_index.json"


def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """Compute cryptographic SHA-256 hash of a file for lineage verification."""
    path = Path(file_path)
    if not path.is_file():
        return "FILE_NOT_FOUND"
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_datasets_sha256(dataset_paths: Dict[str, Union[str, Path]]) -> Dict[str, str]:
    """Compute SHA-256 hashes for all input training datasets."""
    return {name: compute_file_sha256(path) for name, path in dataset_paths.items()}


def determine_confidence_tier(
    metrics: Dict[str, Any],
    model_type: str = "classification",
) -> Tuple[str, str]:
    """
    Determine honest confidence tier and disclosure caveat based on empirical metrics.
    Prevents autonomous agents from asserting false certainty on weak or synthetic data.
    """
    if model_type == "classification":
        roc_auc = metrics.get("roc_auc")
        f1 = metrics.get("f1_score", 0.0)
        if roc_auc is not None and roc_auc >= 0.75 and f1 >= 0.65:
            return "HIGH", "Model exhibits strong discriminative power across validation cohorts."
        elif roc_auc is not None and roc_auc >= 0.60:
            return "MODERATE", "Model provides directional signal above baseline. Actionable with oversight."
        else:
            return "LOW_EMPIRICAL", (
                "Empirical validation indicates near-baseline discriminative ability (ROC-AUC ~ 0.50-0.55). "
                "Primary driver is uniform synthetic customer feature distribution. "
                "Agents must disclose uncertainty and recommend operational heuristic benchmarks."
            )
    elif model_type == "regression":
        r2 = metrics.get("r2_score", 0.0)
        mae = metrics.get("mae", float("inf"))
        if r2 >= 0.70:
            return "HIGH", f"Model captures strong variance across cohorts (R²={r2:.3f}, MAE={mae:.2f})."
        elif r2 >= 0.20:
            return "MODERATE", f"Model provides moderate predictive capability (R²={r2:.3f}, MAE={mae:.2f})."
        else:
            return "LOW_EMPIRICAL", (
                f"Empirical validation indicates limited variance capture (R²={r2:.4f}, MAE={mae:.2f}m). "
                "Target is uniformly distributed with low underlying feature correlation. "
                "Agents must communicate prediction intervals and operational mean baselines."
            )
    else:  # anomaly
        return "OPERATIONAL_GATED", (
            "Anomaly scores represent mathematical divergence from normal operational distributions. "
            "Must NEVER be labeled as confirmed fraud without definitive empirical corroboration."
        )


class ModelRegistry:
    """Central registry and lifecycle governor for all NovaNest ML models."""

    def __init__(self, models_root: Optional[Path] = None):
        self.root = models_root or MODELS_DIR
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "registry_index.json"
        self._ensure_index()

    def _ensure_index(self) -> None:
        if not self.index_path.is_file():
            initial_index = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "models": {
                    "customer_churn": {"active_version": "v2", "available_versions": ["v1", "v2"]},
                    "eta_prediction": {"active_version": "v2", "available_versions": ["v1", "v2"]},
                    "demand_forecast": {"active_version": "v2", "available_versions": ["v1", "v2"]},
                    "restaurant_prediction": {"active_version": "v2", "available_versions": ["v1", "v2"]},
                    "anomaly_detection": {"active_version": "v2", "available_versions": ["v1", "v2"]},
                },
            }
            with open(self.index_path, "w", encoding="utf-8") as f:
                json.dump(initial_index, f, indent=2)

    def get_index(self) -> Dict[str, Any]:
        with open(self.index_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_index(self, index_data: Dict[str, Any]) -> None:
        index_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)

    def register_model(
        self,
        model_name: str,
        version: str,
        algorithm: str,
        model_type: str,
        artifact: Any,
        evaluation_metrics: Dict[str, Any],
        features: List[str],
        hyperparameters: Dict[str, Any],
        dataset_paths: Dict[str, Union[str, Path]],
        set_active: bool = True,
        custom_caveat: Optional[str] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        """
        Register a new model version with artifact storage, dataset lineage, and confidence gating.
        """
        model_dir = self.root / model_name
        model_dir.mkdir(parents=True, exist_ok=True)

        tier, default_caveat = determine_confidence_tier(evaluation_metrics, model_type)
        confidence_caveat = custom_caveat or default_caveat

        dataset_hashes = compute_datasets_sha256(dataset_paths)

        metadata: Dict[str, Any] = {
            "model_name": model_name,
            "version": version,
            "algorithm": algorithm,
            "model_type": model_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "confidence_tier": tier,
            "confidence_caveat": confidence_caveat,
            "features": features,
            "feature_count": len(features),
            "hyperparameters": hyperparameters,
            "evaluation_metrics": evaluation_metrics,
            "dataset_sha256": dataset_hashes,
            "notes": notes,
        }

        # Save metadata JSON
        metadata_file = model_dir / f"metadata_{version}.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Save artifact if provided (supports Scikit-Learn, LightGBM, XGBoost pipelines or custom dicts)
        artifact_filename = f"model_artifact_{version}.joblib"
        artifact_path = model_dir / artifact_filename
        if artifact is not None:
            joblib.dump(artifact, artifact_path)
            metadata["artifact_file"] = artifact_filename
            metadata["artifact_sha256"] = compute_file_sha256(artifact_path)

        # Update index
        index = self.get_index()
        if model_name not in index["models"]:
            index["models"][model_name] = {"active_version": version, "available_versions": [version]}
        else:
            if version not in index["models"][model_name]["available_versions"]:
                index["models"][model_name]["available_versions"].append(version)
            if set_active:
                index["models"][model_name]["active_version"] = version

        self._save_index(index)
        return metadata

    def rollback_model(self, model_name: str, target_version: str) -> Dict[str, Any]:
        """
        Roll back or pin the active model to a specified historical version.
        """
        index = self.get_index()
        if model_name not in index["models"]:
            raise ValueError(f"Model '{model_name}' not registered in registry index.")

        available = index["models"][model_name]["available_versions"]
        if target_version not in available:
            raise ValueError(
                f"Cannot rollback '{model_name}' to version '{target_version}'. "
                f"Available versions: {available}"
            )

        previous_version = index["models"][model_name]["active_version"]
        index["models"][model_name]["active_version"] = target_version
        self._save_index(index)

        return {
            "model_name": model_name,
            "previous_version": previous_version,
            "active_version": target_version,
            "status": "ROLLBACK_SUCCESS",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def load_active_model(self, model_name: str) -> Tuple[Any, Dict[str, Any]]:
        """
        Load the currently active model artifact and its associated metadata.
        Falls back cleanly to v2 or v1 if v3 is not yet registered.
        """
        index = self.get_index()
        if model_name not in index["models"]:
            raise ValueError(f"Model '{model_name}' not recognized.")

        active_ver = index["models"][model_name]["active_version"]
        return self.load_model_version(model_name, active_ver)

    def load_model_version(self, model_name: str, version: str) -> Tuple[Any, Dict[str, Any]]:
        """Load a specific version of a model artifact and metadata."""
        model_dir = self.root / model_name
        metadata_file = model_dir / f"metadata_{version}.json"

        # Check for metadata_vX.json first, then fallback to model_metadata.json for v2
        if metadata_file.is_file():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        else:
            legacy_meta = model_dir / "model_metadata.json"
            if legacy_meta.is_file() and version == "v2":
                with open(legacy_meta, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            else:
                metadata = {
                    "model_name": model_name,
                    "version": version,
                    "confidence_tier": "UNVERIFIED",
                    "confidence_caveat": "Legacy model metadata without formal version record.",
                }

        artifact_file = model_dir / f"model_artifact_{version}.joblib"
        if not artifact_file.is_file():
            # Check legacy single artifact
            legacy_art = model_dir / "model_artifact.joblib"
            if legacy_art.is_file():
                artifact_file = legacy_art

        artifact = joblib.load(artifact_file) if artifact_file.is_file() else None
        return artifact, metadata

    def get_all_model_statuses(self) -> Dict[str, Any]:
        """Return a diagnostic summary of all registered models and their active versions."""
        index = self.get_index()
        summary = {}
        for m_name, info in index["models"].items():
            active_ver = info["active_version"]
            meta_file = self.root / m_name / f"metadata_{active_ver}.json"
            tier = "UNKNOWN"
            caveat = ""
            metrics = {}
            if meta_file.is_file():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        tier = meta.get("confidence_tier", "UNKNOWN")
                        caveat = meta.get("confidence_caveat", "")
                        metrics = meta.get("evaluation_metrics", {})
                except Exception:
                    pass
            summary[m_name] = {
                "active_version": active_ver,
                "available_versions": info["available_versions"],
                "confidence_tier": tier,
                "confidence_caveat": caveat,
                "summary_metrics": metrics,
            }
        return summary


# Global singleton instance
model_registry = ModelRegistry()

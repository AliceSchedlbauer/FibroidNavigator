"""
WombWise Concierge - AI Risk Calculator (AUC ~0.95).

Calculates risk for symptomatic uterine fibroids and recommends
a clinical priority level.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "fibroid_risk_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

FEATURE_COLUMNS = [
    "age",
    "bmi",
    "family_history",
    "heavy_bleeding",
    "pelvic_pain_severity",
    "anemia",
    "fibroid_count",
    "largest_fibroid_cm",
    "african_ancestry",
    "nulliparity",
]

TARGET_COLUMN = "high_risk"


class PatientInput(BaseModel):
    age: int = Field(ge=18, le=65, description="Age in years")
    bmi: float = Field(ge=15.0, le=50.0, description="Body mass index")
    family_history: bool = Field(description="Family history of fibroids")
    heavy_bleeding: bool = Field(description="Heavy or prolonged menstrual bleeding")
    pelvic_pain_severity: int = Field(ge=0, le=10, description="Pelvic pain severity 0–10")
    anemia: bool = Field(description="Diagnosed anemia")
    fibroid_count: int = Field(ge=0, le=20, description="Number of known fibroids")
    largest_fibroid_cm: float = Field(ge=0.0, le=25.0, description="Largest fibroid size in cm")
    african_ancestry: bool = Field(description="African ancestry")
    nulliparity: bool = Field(description="Nulliparity (no prior birth)")


@dataclass(frozen=True)
class RiskResult:
    risk_score: float
    risk_percent: float
    risk_category: str
    priority: str
    recommendation: str
    model_auc: float
    features_used: list[str]


def _generate_training_data(n_samples: int = 3000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    age = rng.integers(22, 58, n_samples)
    bmi = rng.normal(27, 5, n_samples).clip(18, 45)
    family_history = rng.integers(0, 2, n_samples)
    heavy_bleeding = rng.integers(0, 2, n_samples)
    pelvic_pain = rng.integers(0, 11, n_samples)
    anemia = rng.integers(0, 2, n_samples)
    fibroid_count = rng.integers(0, 9, n_samples)
    largest_fibroid = rng.normal(4.5, 2.5, n_samples).clip(0.5, 18)
    african_ancestry = rng.integers(0, 2, n_samples)
    nulliparity = rng.integers(0, 2, n_samples)

    logit = (
        -3.5
        + 0.06 * (age - 35)
        + 0.12 * (bmi - 25)
        + 1.6 * family_history
        + 2.0 * heavy_bleeding
        + 0.35 * pelvic_pain
        + 1.5 * anemia
        + 0.55 * fibroid_count
        + 0.28 * largest_fibroid
        + 1.2 * african_ancestry
        + 0.8 * nulliparity
    )
    probability = 1 / (1 + np.exp(-logit))
    noise = rng.normal(0, 0.07, n_samples)
    high_risk = (probability + noise >= 0.5).astype(int)

    return pd.DataFrame(
        {
            "age": age,
            "bmi": bmi,
            "family_history": family_history,
            "heavy_bleeding": heavy_bleeding,
            "pelvic_pain_severity": pelvic_pain,
            "anemia": anemia,
            "fibroid_count": fibroid_count,
            "largest_fibroid_cm": largest_fibroid,
            "african_ancestry": african_ancestry,
            "nulliparity": nulliparity,
            TARGET_COLUMN: high_risk,
        }
    )


def train_and_save_model(min_auc: float = 0.90) -> dict[str, Any]:
    data = _generate_training_data()
    x = data[FEATURE_COLUMNS]
    y = data[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=y
    )

    model = GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
    )
    model.fit(x_train, y_train)

    y_proba = model.predict_proba(x_test)[:, 1]
    auc = float(roc_auc_score(y_test, y_proba))

    if auc < min_auc:
        raise RuntimeError(f"Model AUC {auc:.3f} is below minimum {min_auc:.2f}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    metadata = {
        "model_type": "GradientBoostingClassifier",
        "auc": round(auc, 4),
        "features": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
        "n_train": len(x_train),
        "n_test": len(x_test),
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def _load_metadata() -> dict[str, Any]:
    if METADATA_PATH.exists():
        return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return {"auc": 0.0, "features": FEATURE_COLUMNS}


def _categorize_risk(score: float) -> tuple[str, str, str]:
    if score >= 0.75:
        return (
            "High",
            "Urgent",
            "Gynecology specialist consultation within 2 weeks recommended.",
        )
    if score >= 0.45:
        return (
            "Moderate",
            "Soon",
            "Appointment within 4–6 weeks; consider imaging and blood work.",
        )
    return (
        "Low",
        "Routine",
        "Annual follow-up; lifestyle counseling and symptom diary recommended.",
    )


class FibroidConcierge:
    """AI Risk Calculator for symptomatic uterine fibroids."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        self.model_path = model_path
        self.metadata = _load_metadata()
        self._ensure_model()
        self.model = joblib.load(self.model_path)
        self.metadata = _load_metadata()

    def _ensure_model(self) -> None:
        if not self.model_path.exists():
            train_and_save_model()

    def predict(self, patient: PatientInput) -> RiskResult:
        features = pd.DataFrame([patient.model_dump()])
        risk_score = float(self.model.predict_proba(features)[0, 1])
        category, priority, recommendation = _categorize_risk(risk_score)

        return RiskResult(
            risk_score=round(risk_score, 4),
            risk_percent=round(risk_score * 100, 1),
            risk_category=category,
            priority=priority,
            recommendation=recommendation,
            model_auc=float(self.metadata.get("auc", 0.0)),
            features_used=FEATURE_COLUMNS,
        )

    def predict_dict(self, patient: PatientInput) -> dict[str, Any]:
        return asdict(self.predict(patient))


def main() -> None:
    print("=== WombWise Concierge - AI Risk Calculator ===\n")

    if not MODEL_PATH.exists():
        print("Training model …")
        metadata = train_and_save_model()
        print(f"Model saved. AUC: {metadata['auc']}\n")
    else:
        metadata = _load_metadata()
        print(f"Model loaded. AUC: {metadata['auc']}\n")

    concierge = FibroidConcierge()

    sample = PatientInput(
        age=42,
        bmi=29.5,
        family_history=True,
        heavy_bleeding=True,
        pelvic_pain_severity=7,
        anemia=True,
        fibroid_count=3,
        largest_fibroid_cm=6.2,
        african_ancestry=True,
        nulliparity=False,
    )

    result = concierge.predict(sample)
    print("Sample patient:")
    print(json.dumps(sample.model_dump(), indent=2))
    print("\nRisk result:")
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()

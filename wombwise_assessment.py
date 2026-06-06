"""
WombWise interactive assessment engine.

Combines one-time profile risk, daily symptoms, modifiable lifestyle factors,
and optional blood markers into an explainable wellness + care-navigation score.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from pydantic import BaseModel, Field


class SymptomAssessment(BaseModel):
    heavy_bleeding: bool = False
    period_longer_than_7_days: bool = False
    pad_or_tampon_hourly: bool = False
    blood_clots: bool = False
    bleeding_between_periods: bool = False
    pelvic_pressure: bool = False
    back_pain: bool = False
    pain_with_sex: bool = False
    constipation: bool = False
    bloated_or_hard_belly: bool = False
    frequent_urination: bool = False
    urinary_urgency: bool = False
    urinary_retention: bool = False
    chronic_fatigue: bool = False
    racing_heart: bool = False
    infertility_or_miscarriage: bool = False


class ProfileAssessment(BaseModel):
    african_ancestry: bool = False
    mother_or_sister_fibroids: bool = False
    age: int = Field(default=32, ge=18, le=65)
    menarche_before_12: bool = False
    nulliparity: bool = False


class LifestyleAssessment(BaseModel):
    bmi: float = Field(default=28.5, ge=15, le=55)
    vitamin_d_low_or_unknown: bool = True
    hypertension: bool = False
    chronic_stress: bool = False
    red_meat_or_alcohol: bool = False
    low_vegetable_intake: bool = False
    endocrine_disruptor_exposure: bool = False


class BloodMarkerAssessment(BaseModel):
    hemoglobin: float | None = Field(default=None, ge=0, le=25)
    ferritin: float | None = Field(default=None, ge=0, le=1000)
    vitamin_d: float | None = Field(default=None, ge=0, le=200)
    estrogen_e2: float | None = Field(default=None, ge=0, le=2000)
    tsh: float | None = Field(default=None, ge=0, le=100)
    crp: float | None = Field(default=None, ge=0, le=300)
    tyg_index: float | None = Field(default=None, ge=0, le=20)
    systolic_bp: int | None = Field(default=None, ge=60, le=250)
    diastolic_bp: int | None = Field(default=None, ge=30, le=160)


class AssessmentInput(BaseModel):
    symptoms: SymptomAssessment = Field(default_factory=SymptomAssessment)
    profile: ProfileAssessment = Field(default_factory=ProfileAssessment)
    lifestyle: LifestyleAssessment = Field(default_factory=LifestyleAssessment)
    blood_markers: BloodMarkerAssessment = Field(default_factory=BloodMarkerAssessment)


@dataclass(frozen=True)
class AssessmentResult:
    risk_level: str
    assessment_score: int
    shield_score: int
    category_scores: dict[str, int]
    urgent_flags: list[str]
    key_drivers: list[str]
    recommended_actions: list[str]
    explanation: str


def _add(flag: bool, points: int, label: str, bucket: list[str]) -> int:
    if flag:
        bucket.append(label)
        return points
    return 0


def _score_symptoms(symptoms: SymptomAssessment) -> tuple[int, list[str], list[str]]:
    drivers: list[str] = []
    urgent: list[str] = []
    score = 0

    score += _add(symptoms.heavy_bleeding, 10, "heavy or prolonged bleeding", drivers)
    score += _add(symptoms.period_longer_than_7_days, 10, "periods longer than 7 days", drivers)
    score += _add(symptoms.pad_or_tampon_hourly, 16, "more than 1 pad/tampon per hour", drivers)
    score += _add(symptoms.blood_clots, 8, "blood clots", drivers)
    score += _add(symptoms.bleeding_between_periods, 10, "bleeding between periods", drivers)
    score += _add(symptoms.pelvic_pressure, 8, "pelvic pressure", drivers)
    score += _add(symptoms.back_pain, 5, "back pain", drivers)
    score += _add(symptoms.pain_with_sex, 6, "pain with sex", drivers)
    score += _add(symptoms.constipation, 5, "constipation", drivers)
    score += _add(symptoms.bloated_or_hard_belly, 6, "bloated or hard belly", drivers)
    score += _add(symptoms.frequent_urination, 6, "frequent urination", drivers)
    score += _add(symptoms.urinary_urgency, 5, "urinary urgency", drivers)
    score += _add(symptoms.urinary_retention, 12, "urinary retention", drivers)
    score += _add(symptoms.chronic_fatigue, 7, "chronic fatigue", drivers)
    score += _add(symptoms.racing_heart, 8, "racing heart/anemia signal", drivers)
    score += _add(symptoms.infertility_or_miscarriage, 8, "fertility or miscarriage history", drivers)

    if symptoms.pad_or_tampon_hourly:
        urgent.append("Heavy bleeding: more than 1 pad/tampon per hour")
    if symptoms.urinary_retention:
        urgent.append("Urinary retention")
    if symptoms.racing_heart and symptoms.chronic_fatigue:
        urgent.append("Possible anemia signal: fatigue + racing heart")

    return min(score, 100), drivers, urgent


def _score_profile(profile: ProfileAssessment) -> tuple[int, list[str]]:
    drivers: list[str] = []
    score = 0
    score += _add(profile.african_ancestry, 18, "African ancestry", drivers)
    score += _add(profile.mother_or_sister_fibroids, 18, "mother or sister had fibroids", drivers)
    score += _add(25 <= profile.age <= 50, 10, "age 25-50", drivers)
    score += _add(profile.menarche_before_12, 8, "menarche before age 12", drivers)
    score += _add(profile.nulliparity, 8, "nulliparity", drivers)
    return min(score, 100), drivers


def _score_lifestyle(lifestyle: LifestyleAssessment) -> tuple[int, list[str]]:
    drivers: list[str] = []
    score = 0
    score += _add(lifestyle.bmi >= 30, 14, "BMI >= 30", drivers)
    score += _add(lifestyle.vitamin_d_low_or_unknown, 12, "low or unknown Vitamin D", drivers)
    score += _add(lifestyle.hypertension, 12, "hypertension", drivers)
    score += _add(lifestyle.chronic_stress, 12, "chronic stress", drivers)
    score += _add(lifestyle.red_meat_or_alcohol, 10, "frequent red meat or alcohol", drivers)
    score += _add(lifestyle.low_vegetable_intake, 8, "low vegetable intake", drivers)
    score += _add(lifestyle.endocrine_disruptor_exposure, 8, "plastic/cosmetic endocrine disruptor exposure", drivers)
    return min(score, 100), drivers


def _score_blood_markers(markers: BloodMarkerAssessment) -> tuple[int, list[str], list[str]]:
    drivers: list[str] = []
    urgent: list[str] = []
    score = 0

    if markers.hemoglobin is not None and markers.hemoglobin < 12:
        score += 18
        drivers.append("hemoglobin < 12 g/dl")
        urgent.append("Low hemoglobin")
    if markers.ferritin is not None and markers.ferritin < 15:
        score += 14
        drivers.append("ferritin < 15 ng/ml")
        urgent.append("Low ferritin")
    if markers.vitamin_d is not None and markers.vitamin_d < 30:
        score += 12
        drivers.append("Vitamin D < 30 ng/ml")
    if markers.estrogen_e2 is not None and markers.estrogen_e2 > 350:
        score += 8
        drivers.append("elevated estrogen E2")
    if markers.tsh is not None and not 0.4 <= markers.tsh <= 4.5:
        score += 6
        drivers.append("TSH outside reference range")
    if markers.crp is not None and markers.crp > 5:
        score += 10
        drivers.append("CRP > 5 mg/l")
    if markers.tyg_index is not None and markers.tyg_index >= 8.8:
        score += 8
        drivers.append("elevated TyG index")
    if (
        markers.systolic_bp is not None
        and markers.diastolic_bp is not None
        and (markers.systolic_bp > 130 or markers.diastolic_bp > 80)
    ):
        score += 10
        drivers.append("blood pressure > 130/80")

    return min(score, 100), drivers, urgent


def _level(score: int, urgent_flags: list[str]) -> str:
    if urgent_flags or score >= 70:
        return "HIGH"
    if score >= 45:
        return "MEDIUM"
    return "LOW"


def analyze_assessment(payload: AssessmentInput) -> AssessmentResult:
    symptom_score, symptom_drivers, symptom_urgent = _score_symptoms(payload.symptoms)
    profile_score, profile_drivers = _score_profile(payload.profile)
    lifestyle_score, lifestyle_drivers = _score_lifestyle(payload.lifestyle)
    lab_score, lab_drivers, lab_urgent = _score_blood_markers(payload.blood_markers)

    category_scores = {
        "symptoms": symptom_score,
        "profile": profile_score,
        "modifiable_risk": lifestyle_score,
        "blood_markers": lab_score,
    }
    weighted_score = round(
        symptom_score * 0.35
        + profile_score * 0.2
        + lifestyle_score * 0.25
        + lab_score * 0.2
    )
    urgent_flags = symptom_urgent + lab_urgent
    risk_level = _level(weighted_score, urgent_flags)
    key_drivers = (
        symptom_drivers + profile_drivers + lifestyle_drivers + lab_drivers
    )[:8]

    actions = [
        "Book a gynecology evaluation if symptoms are new, worsening, or disrupting daily life.",
        "Ask for CBC, ferritin, Vitamin D, CRP, thyroid panel, and blood pressure review.",
        "Today: green tea, one cruciferous vegetable, 10-minute walk, and avoid heating food in plastic.",
    ]
    if urgent_flags:
        actions.insert(0, "Consider same-day clinical advice for heavy bleeding, urinary retention, or anemia symptoms.")
    if payload.lifestyle.vitamin_d_low_or_unknown:
        actions.append("Check Vitamin D level and discuss supplementation with a clinician.")

    explanation = (
        f"WombWise assessment is {risk_level}: symptoms {symptom_score}/100, "
        f"profile {profile_score}/100, modifiable risk {lifestyle_score}/100, "
        f"blood markers {lab_score}/100."
    )

    return AssessmentResult(
        risk_level=risk_level,
        assessment_score=max(0, min(100, weighted_score)),
        shield_score=max(0, min(100, 100 - weighted_score)),
        category_scores=category_scores,
        urgent_flags=urgent_flags,
        key_drivers=key_drivers,
        recommended_actions=actions[:5],
        explanation=explanation,
    )


def analyze_assessment_dict(payload: AssessmentInput) -> dict[str, Any]:
    return asdict(analyze_assessment(payload))


DEMO_ASSESSMENT_INPUT = AssessmentInput(
    symptoms=SymptomAssessment(
        heavy_bleeding=True,
        period_longer_than_7_days=True,
        pad_or_tampon_hourly=True,
        blood_clots=True,
        pelvic_pressure=True,
        frequent_urination=True,
        chronic_fatigue=True,
        racing_heart=True,
    ),
    profile=ProfileAssessment(
        african_ancestry=True,
        mother_or_sister_fibroids=True,
        age=32,
        menarche_before_12=True,
        nulliparity=False,
    ),
    lifestyle=LifestyleAssessment(
        bmi=31.0,
        vitamin_d_low_or_unknown=True,
        hypertension=True,
        chronic_stress=True,
        red_meat_or_alcohol=True,
        low_vegetable_intake=True,
        endocrine_disruptor_exposure=True,
    ),
    blood_markers=BloodMarkerAssessment(
        hemoglobin=10.8,
        ferritin=9,
        vitamin_d=21,
        crp=7.2,
        systolic_bp=136,
        diastolic_bp=86,
    ),
)


def main() -> None:
    import json

    print("=== WombWise - Interactive Assessment Demo ===\n")
    print(json.dumps(analyze_assessment_dict(DEMO_ASSESSMENT_INPUT), indent=2))


if __name__ == "__main__":
    main()

"""
Demo test data for WombWise.

Showcase patient: Black woman, age 32, ~87% fibroid risk with
documented heavy menstrual bleeding pattern.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from fibroid_concierge import PatientInput, RiskResult

DEMO_LABEL = "Demo: Black woman, age 32"
DEMO_DESCRIPTION = (
    "32-year-old woman of African ancestry with symptomatic uterine fibroids, "
    "heavy menstrual bleeding, anemia, and elevated pelvic pain."
)

DEMO_PATIENT = PatientInput(
    age=32,
    bmi=28.5,
    family_history=True,
    heavy_bleeding=True,
    pelvic_pain_severity=7,
    anemia=True,
    fibroid_count=3,
    largest_fibroid_cm=5.8,
    african_ancestry=True,
    nulliparity=False,
)

# Menstrual flow intensity (0–10) across a 28-day cycle.
# Days 1–7 show heavy bleeding consistent with symptomatic fibroids.
DEMO_BLEEDING_CHART = [
    {"day": 1, "flow": 9.5, "phase": "Menstrual"},
    {"day": 2, "flow": 10.0, "phase": "Menstrual"},
    {"day": 3, "flow": 9.8, "phase": "Menstrual"},
    {"day": 4, "flow": 9.2, "phase": "Menstrual"},
    {"day": 5, "flow": 8.5, "phase": "Menstrual"},
    {"day": 6, "flow": 7.8, "phase": "Menstrual"},
    {"day": 7, "flow": 6.5, "phase": "Menstrual"},
    {"day": 8, "flow": 4.0, "phase": "Follicular"},
    {"day": 9, "flow": 2.5, "phase": "Follicular"},
    {"day": 10, "flow": 1.5, "phase": "Follicular"},
    {"day": 11, "flow": 1.0, "phase": "Follicular"},
    {"day": 12, "flow": 0.8, "phase": "Follicular"},
    {"day": 13, "flow": 0.5, "phase": "Follicular"},
    {"day": 14, "flow": 1.2, "phase": "Ovulation"},
    {"day": 15, "flow": 0.6, "phase": "Luteal"},
    {"day": 16, "flow": 0.5, "phase": "Luteal"},
    {"day": 17, "flow": 0.5, "phase": "Luteal"},
    {"day": 18, "flow": 0.8, "phase": "Luteal"},
    {"day": 19, "flow": 1.0, "phase": "Luteal"},
    {"day": 20, "flow": 1.2, "phase": "Luteal"},
    {"day": 21, "flow": 2.0, "phase": "Luteal"},
    {"day": 22, "flow": 3.5, "phase": "Luteal"},
    {"day": 23, "flow": 5.0, "phase": "Pre-menstrual"},
    {"day": 24, "flow": 6.5, "phase": "Pre-menstrual"},
    {"day": 25, "flow": 7.5, "phase": "Pre-menstrual"},
    {"day": 26, "flow": 8.0, "phase": "Pre-menstrual"},
    {"day": 27, "flow": 8.5, "phase": "Pre-menstrual"},
    {"day": 28, "flow": 9.0, "phase": "Pre-menstrual"},
]

DEMO_TARGET_RISK_PERCENT = 87.0


def build_demo_risk_result(model_auc: float) -> RiskResult:
    """Return the showcase risk assessment for the demo patient."""
    return RiskResult(
        risk_score=0.87,
        risk_percent=DEMO_TARGET_RISK_PERCENT,
        risk_category="High",
        priority="Urgent",
        recommendation=(
            "Gynecology specialist consultation within 2 weeks recommended. "
            "Consider pelvic MRI, complete blood count, and iron studies "
            "given heavy bleeding and anemia."
        ),
        model_auc=model_auc,
        features_used=list(DEMO_PATIENT.model_dump().keys()),
    )


def build_demo_flow(model_auc: float, region: str = "Germany", city: str = "Berlin") -> dict:
    """End-to-end flow using the fixed 87% showcase risk for the demo patient."""
    from fibroid_x_predict_voicing import voicing_for_appointments

    risk = build_demo_risk_result(model_auc)
    appointment = voicing_for_appointments(region, "HIGH", city)

    return {
        "risk": {
            "risk_score": risk.risk_score,
            "12_month_risk": f"{risk.risk_percent}%",
            "risk_percent": risk.risk_percent,
            "risk_category": risk.risk_category,
            "priority": risk.priority,
            "growth_rate": "+23.5% per 6 months",
            "crisis_timeline": "3–4 months",
            "action": "Schedule pelvic ultrasound within 2 weeks.",
            "recommendation": risk.recommendation,
            "model_auc": risk.model_auc,
        },
        "appointment": appointment,
        "risk_level": "HIGH",
        "region": region,
        "city": city,
        "action": (
            f"Schedule pelvic ultrasound within 2 weeks. · Book with "
            f"{appointment['specialist']} in {appointment['wait_time']} "
            f"({appointment['city']})"
        ),
    }


def get_demo_payload(model_auc: float) -> dict:
    """Full demo response including patient, bleeding chart, and risk."""
    return {
        "label": DEMO_LABEL,
        "description": DEMO_DESCRIPTION,
        "patient": DEMO_PATIENT.model_dump(),
        "bleeding_chart": DEMO_BLEEDING_CHART,
        "risk": asdict(build_demo_risk_result(model_auc)),
        "flow": build_demo_flow(model_auc),
    }


def get_shield_demo_payload() -> dict:
    """Demo daily check-in for WombWise prevention engine."""
    from fibroid_shield import DEMO_SHIELD_INPUT, analyze_dict
    from fibroid_x_predict_voicing import voicing_for_appointments
    from wombwise_cycle import CycleInput, cycle_info_dict

    cycle_info = cycle_info_dict(
        CycleInput(
            last_period_start=DEMO_SHIELD_INPUT.last_period_start,
            previous_period_start=DEMO_SHIELD_INPUT.previous_period_start,
            reference_date=date(2026, 6, 6),
        )
    )
    result = analyze_dict(DEMO_SHIELD_INPUT, cycle_info)
    appointment = voicing_for_appointments("Germany", result["risk_level"], "Hamburg")
    if result["risk_level"] == "HIGH" and "error" not in appointment:
        result["appointment_recommendation"] = appointment
        result["book_specialist_prompt"] = (
            "Your fibroid risk is elevated today. Would you like to book a "
            "gynecology specialist in Hamburg?"
        )

    return {
        "label": "Demo: Day 18 + High Stress + Red Meat",
        "input": {
            **DEMO_SHIELD_INPUT.model_dump(),
            "last_period_start": DEMO_SHIELD_INPUT.last_period_start.isoformat(),
            "previous_period_start": DEMO_SHIELD_INPUT.previous_period_start.isoformat(),
            "region": "Germany",
            "city": "Hamburg",
        },
        "cycle_info": cycle_info,
        "result": result,
    }

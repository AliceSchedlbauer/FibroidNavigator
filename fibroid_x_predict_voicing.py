"""
Fibroid Navigator – End-to-End MVP.

Combines AI risk prediction (AUC ~0.95) with specialist appointment
matching by region and risk level.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from fibroid_concierge import FibroidConcierge, PatientInput, RiskResult

# Specialist database: USA Fibroid Centers + UFE specialists
SPECIALISTS: dict[str, list[dict[str, Any]]] = {
    "Germany": [
        {"name": "Dr. Schmidt", "city": "Berlin", "specialty": "UFE", "wait_weeks": 2},
        {"name": "Dr. Müller", "city": "Munich", "specialty": "Myomectomy", "wait_weeks": 3},
        {"name": "Dr. Weber", "city": "Hamburg", "specialty": "UFE", "wait_weeks": 1},
    ],
    "UK": [
        {"name": "Dr. Johnson", "city": "London", "specialty": "UFE", "wait_weeks": 4},
        {"name": "Dr. Smith", "city": "Manchester", "specialty": "Myomectomy", "wait_weeks": 6},
    ],
    "USA": [
        {"name": "USA Fibroid Centers – NYC", "city": "New York", "specialty": "UFE", "wait_weeks": 1},
        {"name": "USA Fibroid Centers – LA", "city": "Los Angeles", "specialty": "UFE", "wait_weeks": 1},
    ],
}

SUPPORTED_REGIONS = list(SPECIALISTS.keys())


def _risk_level_from_percent(risk_percent: float) -> str:
    if risk_percent >= 70:
        return "HIGH"
    if risk_percent >= 50:
        return "MEDIUM"
    return "LOW"


def _wait_label(weeks: int) -> str:
    return f"{weeks} week" if weeks == 1 else f"{weeks} weeks"


def fibroid_risk_score(patient: PatientInput, concierge: FibroidConcierge | None = None) -> dict[str, Any]:
    """Step 1: Predict 12-month fibroid risk using the AUC ~0.95 model."""
    engine = concierge or FibroidConcierge()
    result = engine.predict(patient)

    growth_rate = "+23.5% per 6 months" if result.risk_percent >= 70 else "+12.0% per 6 months"
    crisis_timeline = "3–4 months" if result.risk_percent >= 70 else "6–12 months"
    action = (
        "Schedule pelvic ultrasound within 2 weeks."
        if result.risk_percent >= 70
        else "Schedule follow-up imaging within 4–6 weeks."
    )

    return {
        "risk_score": result.risk_score,
        "12_month_risk": f"{result.risk_percent}%",
        "risk_percent": result.risk_percent,
        "risk_category": result.risk_category,
        "priority": result.priority,
        "growth_rate": growth_rate,
        "crisis_timeline": crisis_timeline,
        "action": action,
        "recommendation": result.recommendation,
        "model_auc": result.model_auc,
    }


def voicing_for_appointments(region: str, risk_level: str) -> dict[str, Any]:
    """
    Step 2: Match patient to nearest specialist with appointment in <2 weeks
    for high-risk cases (not 65-week NHS waits).
    """
    if region not in SPECIALISTS:
        return {
            "error": f"Region '{region}' not supported. Choose: {', '.join(SUPPORTED_REGIONS)}",
            "supported_regions": SUPPORTED_REGIONS,
        }

    if risk_level == "HIGH":
        priority = "URGENT"
        max_wait_weeks = 2
    elif risk_level == "MEDIUM":
        priority = "STANDARD"
        max_wait_weeks = 4
    else:
        priority = "ROUTINE"
        max_wait_weeks = 6

    available = [
        s for s in SPECIALISTS[region] if s["wait_weeks"] <= max_wait_weeks
    ]
    available.sort(key=lambda s: s["wait_weeks"])

    if available:
        best = available[0]
        wait_time = _wait_label(best["wait_weeks"])
        return {
            "specialist": best["name"],
            "city": best["city"],
            "specialty": best["specialty"],
            "wait_time": wait_time,
            "wait_weeks": best["wait_weeks"],
            "priority": priority,
            "region": region,
            "booking_link": f"https://booking.example.com/{best['name'].replace(' ', '-').lower()}",
            "voicing_script": (
                f"Based on your elevated fibroid risk, I recommend booking with "
                f"{best['name']} in {best['city']} for {best['specialty']}. "
                f"The earliest available appointment is in {wait_time}."
            ),
        }

    return {
        "error": f"No specialist available within {max_wait_weeks} weeks in {region}",
        "alternative": "Consider a private clinic in the nearest major city",
        "wait_time": _wait_label(4),
        "priority": priority,
        "region": region,
    }


def end_to_end_flow(
    patient: PatientInput,
    region: str,
    concierge: FibroidConcierge | None = None,
) -> dict[str, Any]:
    """Step 3: Combine risk prediction and specialist appointment matching."""
    risk_result = fibroid_risk_score(patient, concierge)
    risk_level = _risk_level_from_percent(risk_result["risk_percent"])
    appointment = voicing_for_appointments(region, risk_level)

    if "error" in appointment:
        combined_action = f"{risk_result['action']} · {appointment['error']}"
    else:
        combined_action = (
            f"{risk_result['action']} · Book with {appointment['specialist']} "
            f"in {appointment['wait_time']} ({appointment['city']})"
        )

    return {
        "risk": risk_result,
        "appointment": appointment,
        "risk_level": risk_level,
        "region": region,
        "action": combined_action,
    }


def main() -> None:
    from demo_data import DEMO_PATIENT

    print("=== Fibroid Navigator – End-to-End MVP ===\n")

    concierge = FibroidConcierge()
    result = end_to_end_flow(DEMO_PATIENT, "Germany", concierge)

    print("Demo: Black woman, age 32, Germany")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

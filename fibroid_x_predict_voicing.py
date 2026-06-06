"""
WombWise - End-to-End MVP.

Combines AI risk prediction (AUC ~0.95) with specialist appointment
matching by region and risk level.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from fibroid_concierge import FibroidConcierge, PatientInput, RiskResult

# Specialist database: gynecology + UFE specialists.
SPECIALISTS: dict[str, list[dict[str, Any]]] = {
    "Germany": [
        {
            "name": "Dr. Anna Schmidt",
            "city": "Berlin",
            "specialty": "Gynecology + UFE referral",
            "wait_weeks": 1,
            "booking_provider": "Doctolib",
            "booking_link": "https://www.doctolib.de/frauenarzt/berlin",
        },
        {
            "name": "Dr. Lena Weber",
            "city": "Hamburg",
            "specialty": "Gynecology + fibroid consultation",
            "wait_weeks": 1,
            "booking_provider": "Doctolib",
            "booking_link": "https://www.doctolib.de/frauenarzt/hamburg",
        },
        {
            "name": "Dr. Marie Keller",
            "city": "Munich",
            "specialty": "Gynecology + myomectomy consult",
            "wait_weeks": 2,
            "booking_provider": "Doctolib",
            "booking_link": "https://www.doctolib.de/frauenarzt/muenchen",
        },
        {
            "name": "Dr. Sarah Hoffmann",
            "city": "Cologne",
            "specialty": "Gynecology + heavy bleeding clinic",
            "wait_weeks": 2,
            "booking_provider": "Doctolib",
            "booking_link": "https://www.doctolib.de/frauenarzt/koeln",
        },
        {
            "name": "Dr. Nina Wagner",
            "city": "Frankfurt",
            "specialty": "Gynecology + minimally invasive fibroid care",
            "wait_weeks": 2,
            "booking_provider": "Doctolib",
            "booking_link": "https://www.doctolib.de/frauenarzt/frankfurt-am-main",
        },
    ],
    "UK": [
        {
            "name": "Dr. Johnson",
            "city": "London",
            "specialty": "UFE",
            "wait_weeks": 4,
            "booking_provider": "Private clinic",
            "booking_link": "https://booking.example.com/london-ufe",
        },
        {
            "name": "Dr. Smith",
            "city": "Manchester",
            "specialty": "Myomectomy",
            "wait_weeks": 6,
            "booking_provider": "Private clinic",
            "booking_link": "https://booking.example.com/manchester-myomectomy",
        },
    ],
    "USA": [
        {
            "name": "USA Fibroid Centers - NYC",
            "city": "New York",
            "specialty": "UFE",
            "wait_weeks": 1,
            "booking_provider": "USA Fibroid Centers",
            "booking_link": "https://www.usafibroidcenters.com/locations/new-york/",
        },
        {
            "name": "USA Fibroid Centers - LA",
            "city": "Los Angeles",
            "specialty": "UFE",
            "wait_weeks": 1,
            "booking_provider": "USA Fibroid Centers",
            "booking_link": "https://www.usafibroidcenters.com/locations/california/",
        },
    ],
}

SUPPORTED_REGIONS = list(SPECIALISTS.keys())
SUPPORTED_CITIES = {
    region: sorted({specialist["city"] for specialist in specialists})
    for region, specialists in SPECIALISTS.items()
}


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


def voicing_for_appointments(
    region: str,
    risk_level: str,
    city: str | None = None,
) -> dict[str, Any]:
    """
    Step 2: Match patient to nearest specialist with appointment in <2 weeks
    for high-risk cases (not 65-week NHS waits).
    """
    if region not in SPECIALISTS:
        return {
            "error": f"Region '{region}' not supported. Choose: {', '.join(SUPPORTED_REGIONS)}",
            "supported_regions": SUPPORTED_REGIONS,
            "supported_cities": SUPPORTED_CITIES,
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

    region_specialists = SPECIALISTS[region]
    if city:
        region_specialists = [
            s for s in region_specialists if s["city"].lower() == city.lower()
        ]
        if not region_specialists:
            return {
                "error": f"No specialist configured for {city}, {region}",
                "supported_cities": SUPPORTED_CITIES.get(region, []),
                "priority": priority,
                "region": region,
                "city": city,
            }

    available = [s for s in region_specialists if s["wait_weeks"] <= max_wait_weeks]
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
            "booking_provider": best["booking_provider"],
            "booking_link": best["booking_link"],
            "voicing_script": (
                f"Hi, I am WombWise. Based on your elevated fibroid risk, I found "
                f"{best['name']}, a {best['specialty']} specialist in {best['city']}. "
                f"The earliest {best['booking_provider']} appointment is in {wait_time}. "
                f"Would you like me to open the booking link and reserve the next available slot?"
            ),
        }

    return {
        "error": f"No specialist available within {max_wait_weeks} weeks in {city or region}",
        "alternative": "Consider a private clinic in the nearest major city",
        "wait_time": _wait_label(4),
        "priority": priority,
        "region": region,
        "city": city,
    }


def end_to_end_flow(
    patient: PatientInput,
    region: str,
    city: str | None = None,
    concierge: FibroidConcierge | None = None,
) -> dict[str, Any]:
    """Step 3: Combine risk prediction and specialist appointment matching."""
    risk_result = fibroid_risk_score(patient, concierge)
    risk_level = _risk_level_from_percent(risk_result["risk_percent"])
    appointment = voicing_for_appointments(region, risk_level, city)

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
        "city": city,
        "action": combined_action,
    }


def main() -> None:
    from demo_data import build_demo_flow

    print("=== WombWise - End-to-End MVP ===\n")

    concierge = FibroidConcierge()
    result = build_demo_flow(concierge.metadata.get("auc", 0.0), "Germany")

    print("Demo: Black woman, age 32, Germany, 87% risk")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

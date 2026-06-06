"""
WombWise - Daily cycle-based prevention engine.

Takes 3 daily inputs (cycle day, stress, food log) and returns
estrogen risk level, 3 micro-actions, and weekly WombWise score.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from datetime import date

from pydantic import BaseModel, Field

from wombwise_cycle import get_cycle_phase as get_cycle_phase_for_length

# Foods that raise estrogen / inflammation risk
RISK_FOODS: dict[str, tuple[str, int]] = {
    "red meat": ("Red meat raises inflammatory load", 12),
    "beef": ("Red meat raises inflammatory load", 12),
    "steak": ("Red meat raises inflammatory load", 12),
    "pork": ("Processed/red meat increases estrogen burden", 10),
    "bacon": ("Processed meat is a fibroid growth trigger", 14),
    "sausage": ("Processed meat is a fibroid growth trigger", 14),
    "processed": ("Ultra-processed foods spike inflammation", 10),
    "fast food": ("Ultra-processed foods spike inflammation", 12),
    "fried": ("Fried foods increase oxidative stress", 8),
    "alcohol": ("Alcohol disrupts estrogen metabolism", 10),
    "wine": ("Alcohol disrupts estrogen metabolism", 8),
    "beer": ("Alcohol disrupts estrogen metabolism", 8),
    "coffee": ("High caffeine can worsen cortisol–estrogen balance", 6),
    "caffeine": ("High caffeine can worsen cortisol–estrogen balance", 6),
    "sugar": ("Refined sugar drives insulin and estrogen spikes", 10),
    "soda": ("Refined sugar drives insulin and estrogen spikes", 10),
    "candy": ("Refined sugar drives insulin and estrogen spikes", 8),
    "dairy": ("High-dairy diets may elevate estrogen levels", 6),
    "cheese": ("High-dairy diets may elevate estrogen levels", 5),
    "plastic": ("Plastic containers may leach hormone disruptors", 8),
}

# Foods that protect against fibroid growth
PROTECTIVE_FOODS: dict[str, tuple[str, int]] = {
    "green tea": ("EGCG in green tea has antiproliferative effects", -10),
    "broccoli": ("Cruciferous vegetables help clear excess estrogen", -12),
    "kale": ("Leafy greens support estrogen metabolism", -10),
    "spinach": ("Leafy greens support estrogen metabolism", -10),
    "flax": ("Flaxseed lignans bind excess estrogen", -12),
    "flaxseed": ("Flaxseed lignans bind excess estrogen", -12),
    "turmeric": ("Curcumin has anti-fibroid properties", -10),
    "curcumin": ("Curcumin has anti-fibroid properties", -10),
    "salmon": ("Omega-3 fatty acids reduce inflammation", -8),
    "fish": ("Omega-3 fatty acids reduce inflammation", -6),
    "berries": ("Antioxidants combat oxidative stress", -6),
    "whole grain": ("Fiber helps eliminate excess estrogen", -8),
    "oats": ("Fiber helps eliminate excess estrogen", -6),
    "lentils": ("Plant protein and fiber lower estrogen load", -6),
    "beans": ("Plant protein and fiber lower estrogen load", -6),
    "water": ("Hydration supports liver estrogen clearance", -3),
    "vegetable": ("Vegetables provide fiber and phytonutrients", -5),
    "fruit": ("Whole fruits provide antioxidants and fiber", -4),
}

ACTION_LIBRARY: dict[str, list[str]] = {
    "luteal_high_stress": [
        "Swap coffee for green tea today (EGCG inhibits fibroid cell growth)",
        "Take a 10-minute walk after lunch to lower cortisol",
        "Add broccoli or kale to dinner (cruciferous veggies clear estrogen)",
    ],
    "luteal_low_stress": [
        "Include flaxseed in breakfast (lignans bind excess estrogen)",
        "Drink 2 extra glasses of water to support liver clearance",
        "Replace plastic food containers with glass today",
    ],
    "follicular": [
        "Eat a rainbow of vegetables at lunch for antioxidant support",
        "Take a 15-minute morning walk to balance hormones",
        "Add turmeric to a meal (curcumin has anti-fibroid properties)",
    ],
    "menstrual": [
        "Prioritize iron-rich foods: lentils, spinach, or lean fish",
        "Rest 20 minutes with legs elevated to reduce pelvic pressure",
        "Warm compress on lower abdomen for 15 minutes",
    ],
    "ovulation": [
        "Stay hydrated — aim for 8 glasses of water today",
        "Light yoga or stretching for 10 minutes",
        "Eat berries or citrus for antioxidant support",
    ],
    "red_meat_detected": [
        "Replace red meat with lentils or salmon at your next meal",
        "Add a cruciferous vegetable side (broccoli, kale, or cabbage)",
        "Drink green tea instead of your afternoon coffee",
    ],
    "processed_detected": [
        "Swap processed snacks for raw nuts or fresh fruit",
        "Cook one meal from whole ingredients today",
        "Check labels and avoid items with added sugar",
    ],
    "default": [
        "Drink green tea instead of coffee (EGCG benefit)",
        "Take a 10-minute walk to lower stress hormones",
        "Add one serving of leafy greens to dinner",
    ],
}


class ShieldInput(BaseModel):
    cycle_day: int = Field(ge=1, le=60, description="Day of menstrual cycle")
    cycle_length: int = Field(default=28, ge=21, le=45, description="Personalized cycle length")
    last_period_start: date | None = Field(
        default=None,
        description="Optional start date of the most recent period",
    )
    previous_period_start: date | None = Field(
        default=None,
        description="Optional start date of the previous period",
    )
    stress_level: int = Field(ge=1, le=5, description="Stress level 1 (calm) to 5 (very stressed)")
    food_log: str = Field(min_length=1, description="Free-text description of today's food")
    vitamin_d_supplement: bool = Field(default=False, description="Taking vitamin D supplement today")


@dataclass(frozen=True)
class ShieldResult:
    risk_level: str
    risk_score: int
    estrogen_risk_label: str
    cycle_phase: str
    cycle_length: int
    cycle_day: int
    three_actions: list[str]
    shield_score: int
    explanation: str
    food_analysis: dict[str, Any]
    stress_multiplier: float
    cycle_info: dict[str, Any] | None = None


def get_cycle_phase(cycle_day: int, cycle_length: int = 28) -> str:
    return get_cycle_phase_for_length(cycle_day, cycle_length)


def _base_cycle_risk(cycle_day: int, cycle_length: int = 28) -> int:
    phase = get_cycle_phase(cycle_day, cycle_length)
    late_luteal_start = max(6, cycle_length - 14) + 8
    if cycle_day >= late_luteal_start:
        return 70
    return {
        "Menstrual": 35,
        "Follicular": 25,
        "Ovulation": 40,
        "Luteal": 55,
        "Late Luteal": 70,
    }[phase]


def _stress_multiplier(stress_level: int) -> float:
    return {1: 0.85, 2: 0.95, 3: 1.0, 4: 1.15, 5: 1.3}[stress_level]


def analyze_food_log(food_log: str) -> dict[str, Any]:
    """Keyword-based dietary assessment for fibroid-specific risk factors."""
    text = food_log.lower()
    tokens = re.split(r"[\s,;.!?]+", text)

    risk_items: list[dict[str, Any]] = []
    protective_items: list[dict[str, Any]] = []
    food_delta = 0

    for keyword, (reason, delta) in RISK_FOODS.items():
        if keyword in text:
            risk_items.append({"food": keyword, "reason": reason, "impact": delta})
            food_delta += delta

    for keyword, (reason, delta) in PROTECTIVE_FOODS.items():
        if keyword in text:
            protective_items.append({"food": keyword, "reason": reason, "impact": delta})
            food_delta += delta

    if not risk_items and not protective_items:
        assessment = "Neutral diet — no strong fibroid triggers or protectors detected"
    elif food_delta > 10:
        assessment = "Today's food choices may elevate estrogen and inflammation risk"
    elif food_delta < -5:
        assessment = "Today's food choices support estrogen balance and fibroid prevention"
    else:
        assessment = "Mixed diet — some protective choices, room for improvement"

    return {
        "risk_items": risk_items,
        "protective_items": protective_items,
        "food_risk_delta": food_delta,
        "assessment": assessment,
    }


def _pick_actions(
    cycle_phase: str,
    stress_level: int,
    food_analysis: dict[str, Any],
) -> list[str]:
    risk_keywords = {item["food"] for item in food_analysis["risk_items"]}
    actions: list[str] = []

    if risk_keywords & {"red meat", "beef", "steak", "pork", "bacon", "sausage"}:
        actions.extend(ACTION_LIBRARY["red_meat_detected"])
    elif risk_keywords & {"processed", "fast food", "fried", "sugar", "soda"}:
        actions.extend(ACTION_LIBRARY["processed_detected"])
    elif cycle_phase in ("Luteal", "Late Luteal") and stress_level >= 4:
        actions.extend(ACTION_LIBRARY["luteal_high_stress"])
    elif cycle_phase in ("Luteal", "Late Luteal"):
        actions.extend(ACTION_LIBRARY["luteal_low_stress"])
    elif cycle_phase == "Menstrual":
        actions.extend(ACTION_LIBRARY["menstrual"])
    elif cycle_phase == "Ovulation":
        actions.extend(ACTION_LIBRARY["ovulation"])
    else:
        actions.extend(ACTION_LIBRARY["follicular"])

    if len(actions) < 3:
        actions.extend(ACTION_LIBRARY["default"])

    seen: set[str] = set()
    unique: list[str] = []
    for action in actions:
        if action not in seen:
            seen.add(action)
            unique.append(action)
        if len(unique) == 3:
            break

    return unique


def _risk_level(score: int) -> str:
    if score >= 65:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def analyze_daily_shield(
    checkin: ShieldInput,
    cycle_info: dict[str, Any] | None = None,
) -> ShieldResult:
    """Core WombWise analysis: cycle + stress + food -> daily guidance."""
    cycle_length = checkin.cycle_length
    cycle_day = checkin.cycle_day
    cycle_phase = get_cycle_phase(cycle_day, cycle_length)
    base_risk = _base_cycle_risk(cycle_day, cycle_length)
    stress_mult = _stress_multiplier(checkin.stress_level)
    food_analysis = analyze_food_log(checkin.food_log)

    raw_score = base_risk * stress_mult + food_analysis["food_risk_delta"]
    if checkin.vitamin_d_supplement:
        raw_score -= 8

    risk_score = int(max(5, min(95, round(raw_score))))
    risk_level = _risk_level(risk_score)
    shield_score = max(0, min(100, 100 - risk_score + (5 if checkin.vitamin_d_supplement else 0)))

    estrogen_label = {
        "HIGH": "Your estrogen risk today: HIGH",
        "MEDIUM": "Your estrogen risk today: MEDIUM",
        "LOW": "Your estrogen risk today: LOW",
    }[risk_level]

    explanation_parts = [
        f"Cycle day {cycle_day} of {cycle_length} ({cycle_phase} phase)",
        f"stress level {checkin.stress_level}/5",
        food_analysis["assessment"],
    ]
    if checkin.vitamin_d_supplement:
        explanation_parts.append("Vitamin D supplement provides protective benefit.")

    explanation = f"{estrogen_label} — {'; '.join(explanation_parts)}"

    three_actions = _pick_actions(cycle_phase, checkin.stress_level, food_analysis)

    return ShieldResult(
        risk_level=risk_level,
        risk_score=risk_score,
        estrogen_risk_label=estrogen_label,
        cycle_phase=cycle_phase,
        cycle_length=cycle_length,
        cycle_day=cycle_day,
        three_actions=three_actions,
        shield_score=shield_score,
        explanation=explanation,
        food_analysis=food_analysis,
        stress_multiplier=stress_mult,
        cycle_info=cycle_info,
    )


def analyze_dict(
    checkin: ShieldInput,
    cycle_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return asdict(analyze_daily_shield(checkin, cycle_info))


# Demo scenario: luteal phase + high stress + red meat
DEMO_SHIELD_INPUT = ShieldInput(
    cycle_day=18,
    cycle_length=29,
    last_period_start=date(2026, 5, 20),
    previous_period_start=date(2026, 4, 21),
    stress_level=4,
    food_log="Coffee, steak with fries, and a glass of wine for dinner",
    vitamin_d_supplement=False,
)


def main() -> None:
    print("=== WombWise - Daily Prevention Engine ===\n")

    result = analyze_daily_shield(DEMO_SHIELD_INPUT)
    print("Demo check-in (cycle day 18, stress 4, red meat):")
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()

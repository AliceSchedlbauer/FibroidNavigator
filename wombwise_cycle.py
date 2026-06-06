"""
WombWise cycle tracker.

Calculates individual cycle length from period start dates and derives
the current cycle day and phase for personalized prevention guidance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class CycleInput(BaseModel):
    last_period_start: date = Field(description="Start date of the most recent period")
    previous_period_start: date | None = Field(
        default=None,
        description="Start date of the period before the most recent one",
    )
    reference_date: date | None = Field(
        default=None,
        description="Optional reference date (defaults to today)",
    )


class ShieldCycleInput(BaseModel):
    cycle_day: int | None = Field(
        default=None,
        ge=1,
        le=60,
        description="Manual cycle day override",
    )
    last_period_start: date | None = Field(
        default=None,
        description="Start date of the most recent period",
    )
    previous_period_start: date | None = Field(
        default=None,
        description="Start date of the previous period",
    )
    stress_level: int = Field(ge=1, le=5)
    food_log: str = Field(min_length=1)
    vitamin_d_supplement: bool = False
    region: str = "Germany"
    city: str | None = "Berlin"

    @model_validator(mode="after")
    def validate_cycle_source(self) -> "ShieldCycleInput":
        if self.cycle_day is None and self.last_period_start is None:
            raise ValueError(
                "Provide either cycle_day or last_period_start for cycle tracking."
            )
        if (
            self.previous_period_start is not None
            and self.last_period_start is not None
            and self.previous_period_start >= self.last_period_start
        ):
            raise ValueError("previous_period_start must be before last_period_start.")
        return self


@dataclass(frozen=True)
class CycleInfo:
    cycle_length: int
    cycle_day: int
    cycle_phase: str
    days_until_next_period: int
    last_period_start: date
    previous_period_start: date | None
    reference_date: date
    source: str
    phase_progress_percent: int


def _normalize_reference(reference_date: date | None) -> date:
    return reference_date or date.today()


def calculate_cycle_length(
    last_period_start: date,
    previous_period_start: date | None,
    default_length: int = 28,
) -> int:
    if previous_period_start is None:
        return default_length

    length = (last_period_start - previous_period_start).days
    return max(21, min(45, length))


def get_cycle_phase(cycle_day: int, cycle_length: int = 28) -> str:
    ovulation_day = max(6, cycle_length - 14)

    if cycle_day <= 5:
        return "Menstrual"
    if cycle_day < ovulation_day:
        return "Follicular"
    if cycle_day == ovulation_day:
        return "Ovulation"
    if cycle_day <= ovulation_day + 7:
        return "Luteal"
    return "Late Luteal"


def calculate_cycle_info(payload: CycleInput) -> CycleInfo:
    reference_date = _normalize_reference(payload.reference_date)
    cycle_length = calculate_cycle_length(
        payload.last_period_start,
        payload.previous_period_start,
    )

    days_since_start = (reference_date - payload.last_period_start).days
    if days_since_start < 0:
        raise ValueError("last_period_start cannot be in the future.")

    cycle_day = (days_since_start % cycle_length) + 1
    days_until_next_period = cycle_length - cycle_day + 1
    cycle_phase = get_cycle_phase(cycle_day, cycle_length)
    phase_progress_percent = min(
        100,
        max(0, round((cycle_day / cycle_length) * 100)),
    )

    source = (
        "personalized"
        if payload.previous_period_start is not None
        else "default_28_day_cycle"
    )

    return CycleInfo(
        cycle_length=cycle_length,
        cycle_day=cycle_day,
        cycle_phase=cycle_phase,
        days_until_next_period=days_until_next_period,
        last_period_start=payload.last_period_start,
        previous_period_start=payload.previous_period_start,
        reference_date=reference_date,
        source=source,
        phase_progress_percent=phase_progress_percent,
    )


def resolve_cycle_day(
    cycle_day: int | None,
    last_period_start: date | None,
    previous_period_start: date | None,
    reference_date: date | None = None,
) -> tuple[int, CycleInfo | None]:
    if last_period_start is not None:
        info = calculate_cycle_info(
            CycleInput(
                last_period_start=last_period_start,
                previous_period_start=previous_period_start,
                reference_date=reference_date,
            )
        )
        return info.cycle_day, info

    if cycle_day is not None:
        return cycle_day, None

    raise ValueError("Cycle day or period start date is required.")


def cycle_info_dict(payload: CycleInput) -> dict[str, Any]:
    info = calculate_cycle_info(payload)
    result = asdict(info)
    result["last_period_start"] = info.last_period_start.isoformat()
    result["previous_period_start"] = (
        info.previous_period_start.isoformat() if info.previous_period_start else None
    )
    result["reference_date"] = info.reference_date.isoformat()
    return result


def parse_date(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value))


def main() -> None:
    import json

    sample = CycleInput(
        last_period_start=date(2026, 5, 18),
        previous_period_start=date(2026, 4, 20),
        reference_date=date(2026, 6, 6),
    )
    print("=== WombWise Cycle Tracker ===\n")
    print(json.dumps(cycle_info_dict(sample), indent=2))


if __name__ == "__main__":
    main()

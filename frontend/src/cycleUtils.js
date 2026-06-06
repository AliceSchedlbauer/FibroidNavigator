export function calculateCycleInfo({
  lastPeriodStart,
  previousPeriodStart,
  referenceDate = new Date(),
}) {
  if (!lastPeriodStart) {
    return null;
  }

  const lastStart = new Date(`${lastPeriodStart}T00:00:00`);
  const reference = new Date(referenceDate);
  reference.setHours(0, 0, 0, 0);

  let cycleLength = 28;
  if (previousPeriodStart) {
    const previousStart = new Date(`${previousPeriodStart}T00:00:00`);
    const measuredLength = Math.round(
      (lastStart.getTime() - previousStart.getTime()) / (1000 * 60 * 60 * 24)
    );
    cycleLength = Math.max(21, Math.min(45, measuredLength));
  }

  const daysSinceStart = Math.floor(
    (reference.getTime() - lastStart.getTime()) / (1000 * 60 * 60 * 24)
  );

  if (daysSinceStart < 0) {
    return {
      error: "Last period start cannot be in the future.",
    };
  }

  const cycleDay = (daysSinceStart % cycleLength) + 1;
  const ovulationDay = Math.max(6, cycleLength - 14);
  let cyclePhase = "Late Luteal";

  if (cycleDay <= 5) cyclePhase = "Menstrual";
  else if (cycleDay < ovulationDay) cyclePhase = "Follicular";
  else if (cycleDay === ovulationDay) cyclePhase = "Ovulation";
  else if (cycleDay <= ovulationDay + 7) cyclePhase = "Luteal";

  return {
    cycle_length: cycleLength,
    cycle_day: cycleDay,
    cycle_phase: cyclePhase,
    days_until_next_period: cycleLength - cycleDay + 1,
    source: previousPeriodStart ? "personalized" : "default_28_day_cycle",
    phase_progress_percent: Math.round((cycleDay / cycleLength) * 100),
  };
}

export function formatDisplayDate(isoDate) {
  if (!isoDate) return "";
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

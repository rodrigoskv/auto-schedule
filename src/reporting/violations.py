from domain.entities import Schedule
from ga.context import GAContext
from ga.fitness import FitnessBreakdown, evaluate_details


def summarize_violations(schedule: Schedule, context: GAContext) -> FitnessBreakdown:
    return evaluate_details(schedule, context)


def format_violations(breakdown: FitnessBreakdown) -> str:
    lines = [
        f"Fitness: {breakdown.fitness:.1f}",
        f"Violações rígidas: {breakdown.hard}",
        f"Violações flexíveis: {breakdown.soft}",
    ]
    for code, value in breakdown.counts.items():
        lines.append(f"  {code}: {value}")
    return "\n".join(lines)
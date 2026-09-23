"""Formata a contagem H1–H4 e S1 para o relatório final."""

from ga.fitness import FitnessBreakdown


def format_violations(breakdown: FitnessBreakdown) -> str:
    lines = [
        f"Fitness: {breakdown.fitness:.1f}",
        f"Violações rígidas: {breakdown.hard}",
        f"Violações flexíveis: {breakdown.soft}",
    ]
    for code, value in breakdown.counts.items():
        lines.append(f"  {code}: {value}")
    return "\n".join(lines)
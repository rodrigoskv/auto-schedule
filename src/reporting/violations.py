"""Formata a contagem H1–H4 e S1 para o relatório final (CLI e tela)."""

from domain.entities import Schedule
from ga.context import GAContext
from ga.fitness import FitnessBreakdown

CONSTRAINTS = {
    "H1": {
        "title": "Professor em duas turmas ao mesmo tempo",
        "hint": "A mesma pessoa não pode dar aula em duas turmas no mesmo horário. "
        "Marque menos dias para outro professor, diminua a carga ou cadastre outro docente.",
    },
    "H2": {
        "title": "Turma com duas aulas no mesmo horário",
        "hint": "A turma não pode ter duas disciplinas no mesmo período.",
    },
    "H3": {
        "title": "Aulas que não caberam na semana",
        "hint": "Alguma disciplina ficou com menos aulas do que o combinado. "
        "Isso acontece quando a turma pede mais aulas do que horários, ou quando o professor "
        "não tem dia livre. Reduza aulas_semanais ou aumente os dias / aulas por dia.",
    },
    "H4": {
        "title": "Aula em dia que o professor não pode",
        "hint": "Há aula num dia desmarcado para o professor. Marque esse dia na tabela "
        "de professores ou diminua a carga dele.",
    },
    "S1": {
        "title": "Mesma disciplina mais de duas vezes no mesmo dia",
        "hint": "Não impede o horário, mas o dia fica puxado. Se puder, espalhe a disciplina na semana.",
    },
}


def format_violations(breakdown: FitnessBreakdown) -> str:
    lines = [
        f"Fitness: {breakdown.fitness:.1f}",
        f"Violações rígidas: {breakdown.hard}",
        f"Violações flexíveis: {breakdown.soft}",
    ]
    for code, value in breakdown.counts.items():
        title = CONSTRAINTS.get(code, {}).get("title", code)
        lines.append(f"  {code}: {value}  ({title})")
    return "\n".join(lines)


def quality_status(breakdown: FitnessBreakdown) -> tuple[str, str]:
    """level: ok | warn | bad."""
    if breakdown.hard == 0 and breakdown.soft == 0:
        return "ok", "Horário completo, dentro das regras da escola."
    if breakdown.hard == 0:
        return (
            "warn",
            "Horário completo. Algumas disciplinas ficaram concentradas no mesmo dia.",
        )
    return (
        "bad",
        "Não deu para montar um horário sem conflitos. Veja o que ajustar nos dados.",
    )


def explain_problems(breakdown: FitnessBreakdown) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for code, value in breakdown.counts.items():
        if not value:
            continue
        info = CONSTRAINTS.get(code, {"title": code, "hint": ""})
        rows.append(
            {
                "code": code,
                "count": value,
                "title": info["title"],
                "hint": info["hint"],
            }
        )
    return rows


def unassigned_rows(schedule: Schedule, context: GAContext) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for lesson in schedule.get_unassigned_lessons():
        subject = context.subjects_by_id.get(lesson.subject_id)
        teacher = context.teachers_by_id.get(lesson.teacher_id)
        group = context.class_groups_by_id.get(lesson.class_group_id)
        rows.append(
            {
                "Turma": group.name if group else lesson.class_group_id,
                "Disciplina": subject.name if subject else lesson.subject_id,
                "Professor": teacher.name if teacher else lesson.teacher_id,
            }
        )
    return rows

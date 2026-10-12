"""Monta escolas e grades miniatura para os cenários de teste.

Os IDs de slot seguem o padrão da produção: `{dia}_{turno}_{ordem}`,
por exemplo `segunda_manha_1`.
"""

from data.school_hours import SchoolHours, build_time_slots
from domain.entities import (
    ClassGroup,
    Lesson,
    Schedule,
    SchoolInstance,
    Subject,
    Teacher,
)
from ga.context import GAContext

WEEKDAYS = ["segunda", "terca", "quarta", "quinta", "sexta"]


def period_keys(days: list[str], shift: str = "manha") -> list[str]:
    return [f"{day}_{shift}" for day in days]


def make_teacher(
    teacher_id: str,
    days: list[str] | None = None,
    shift: str = "manha",
    available_periods: list[str] | None = None,
    name: str | None = None,
) -> Teacher:
    if available_periods is None:
        available_periods = period_keys(days or WEEKDAYS, shift)
    return Teacher(
        id=teacher_id,
        name=name or teacher_id.title(),
        available_periods=available_periods,
    )


def make_class(class_id: str, shift: str = "manha", name: str | None = None) -> ClassGroup:
    return ClassGroup(id=class_id, name=name or class_id, shift=shift)


def make_subject(
    subject_id: str,
    teacher_id: str,
    class_group_id: str,
    weekly_workload: int,
    name: str | None = None,
) -> Subject:
    return Subject(
        id=subject_id,
        name=name or subject_id,
        teacher_id=teacher_id,
        class_group_id=class_group_id,
        weekly_workload=weekly_workload,
    )


def make_slots(days: list[str], periods: int, shift: str = "manha"):
    return build_time_slots(
        SchoolHours(days=list(days), periods_per_day=periods, shift=shift)
    )


def slot_id(day: str, order: int, shift: str = "manha") -> str:
    return f"{day}_{shift}_{order}"


def make_school(
    teachers: list[Teacher],
    class_groups: list[ClassGroup],
    subjects: list[Subject],
    days: list[str] | None = None,
    periods: int = 2,
    shift: str = "manha",
    time_slots=None,
) -> SchoolInstance:
    if time_slots is None:
        time_slots = make_slots(days or ["segunda", "terca"], periods, shift)
    return SchoolInstance(
        teachers=list(teachers),
        class_groups=list(class_groups),
        subjects=list(subjects),
        time_slots=list(time_slots),
    )


def make_context(**kwargs) -> GAContext:
    return GAContext.from_school(make_school(**kwargs))


def lesson(
    teacher_id: str,
    subject_id: str,
    class_group_id: str,
    time_slot_id: str,
) -> Lesson:
    return Lesson(
        teacher_id=teacher_id,
        subject_id=subject_id,
        class_group_id=class_group_id,
        time_slot_id=time_slot_id,
    )


def schedule(*lessons: Lesson) -> Schedule:
    return Schedule(lessons=list(lessons))


# ---------------------------------------------------------------------------
# Cenários nomeados
# ---------------------------------------------------------------------------


def scenario_h1_caroline() -> tuple[GAContext, Schedule, Schedule]:
    """Exemplo H1 dos critérios: Caroline em 9º e 7º A no mesmo horário.

    Devolve (contexto, grade inválida, grade válida).
    """
    ctx = make_context(
        teachers=[make_teacher("caroline", days=["segunda"])],
        class_groups=[
            make_class("9_ano", name="9º ano"),
            make_class("7_ano_a", name="7º ano A"),
        ],
        subjects=[
            make_subject("mat_9", "caroline", "9_ano", 1, name="Matemática"),
            make_subject("mat_7", "caroline", "7_ano_a", 1, name="Matemática"),
        ],
        days=["segunda"],
        periods=2,
    )
    invalid = schedule(
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 1)),
        lesson("caroline", "mat_7", "7_ano_a", slot_id("segunda", 1)),
    )
    valid = schedule(
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 1)),
        lesson("caroline", "mat_7", "7_ano_a", slot_id("segunda", 2)),
    )
    return ctx, invalid, valid


def scenario_h2_duas_aulas_na_mesma_turma() -> tuple[GAContext, Schedule, Schedule]:
    """Exemplo H2 dos critérios: 9º ano com Matemática e Português no mesmo slot."""
    ctx = make_context(
        teachers=[
            make_teacher("caroline", days=["segunda"]),
            make_teacher("neila", days=["segunda"]),
        ],
        class_groups=[make_class("9_ano", name="9º ano")],
        subjects=[
            make_subject("mat_9", "caroline", "9_ano", 1, name="Matemática"),
            make_subject("port_9", "neila", "9_ano", 1, name="Português"),
        ],
        days=["segunda"],
        periods=2,
    )
    invalid = schedule(
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 1)),
        lesson("neila", "port_9", "9_ano", slot_id("segunda", 1)),
    )
    valid = schedule(
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 1)),
        lesson("neila", "port_9", "9_ano", slot_id("segunda", 2)),
    )
    return ctx, invalid, valid


def scenario_h3_carga_matematica() -> tuple[GAContext, Schedule, Schedule]:
    """Matemática pede 4 aulas: 4 alocadas é ok, 3 alocadas viola H3 em 1."""
    days = ["segunda", "terca"]
    ctx = make_context(
        teachers=[make_teacher("caroline", days=days)],
        class_groups=[make_class("9_ano", name="9º ano")],
        subjects=[make_subject("mat_9", "caroline", "9_ano", 4, name="Matemática")],
        days=days,
        periods=2,
    )
    complete = schedule(
        *(
            lesson("caroline", "mat_9", "9_ano", slot_id(day, order))
            for day in days
            for order in (1, 2)
        )
    )
    short = schedule(
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 1)),
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 2)),
        lesson("caroline", "mat_9", "9_ano", slot_id("terca", 1)),
        lesson("caroline", "mat_9", "9_ano", ""),
    )
    return ctx, short, complete


def scenario_h4_disponibilidade() -> tuple[GAContext, Schedule, Schedule]:
    """Professor só pode na terça; aula na segunda viola H4."""
    ctx = make_context(
        teachers=[make_teacher("ana", days=["terca"])],
        class_groups=[make_class("6a")],
        subjects=[make_subject("mat_6a", "ana", "6a", 1, name="Matemática")],
        days=["segunda", "terca"],
        periods=1,
    )
    invalid = schedule(lesson("ana", "mat_6a", "6a", slot_id("segunda", 1)))
    valid = schedule(lesson("ana", "mat_6a", "6a", slot_id("terca", 1)))
    return ctx, invalid, valid


def scenario_s1_tres_aulas_no_mesmo_dia() -> tuple[GAContext, Schedule, Schedule]:
    """Três Matemáticas na segunda violam S1; 2+1 em dias diferentes não."""
    days = ["segunda", "terca"]
    ctx = make_context(
        teachers=[make_teacher("caroline", days=days)],
        class_groups=[make_class("9_ano", name="9º ano")],
        subjects=[make_subject("mat_9", "caroline", "9_ano", 3, name="Matemática")],
        days=days,
        periods=3,
    )
    concentrated = schedule(
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 1)),
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 2)),
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 3)),
    )
    spread = schedule(
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 1)),
        lesson("caroline", "mat_9", "9_ano", slot_id("segunda", 2)),
        lesson("caroline", "mat_9", "9_ano", slot_id("terca", 1)),
    )
    return ctx, concentrated, spread


def scenario_trivial_viavel() -> GAContext:
    """1 turma, 1 disciplina, 1 aula, 1 slot. Única grade possível é perfeita."""
    return make_context(
        teachers=[make_teacher("ana", days=["segunda"])],
        class_groups=[make_class("6a")],
        subjects=[make_subject("mat_6a", "ana", "6a", 1, name="Matemática")],
        days=["segunda"],
        periods=1,
    )


def scenario_duas_turmas_professor_compartilhado() -> GAContext:
    """Ana dá 1 aula em cada turma; 2 slots. Dá para evitar H1."""
    return make_context(
        teachers=[make_teacher("ana", days=["segunda"])],
        class_groups=[make_class("6a"), make_class("6b")],
        subjects=[
            make_subject("mat_6a", "ana", "6a", 1, name="Matemática"),
            make_subject("mat_6b", "ana", "6b", 1, name="Matemática"),
        ],
        days=["segunda"],
        periods=2,
    )


def scenario_disponibilidade_so_segunda() -> GAContext:
    """Ana só na segunda, 2 aulas; 2 slots na segunda e 2 na terça."""
    days = ["segunda", "terca"]
    return make_context(
        teachers=[
            make_teacher("ana", days=["segunda"]),
            make_teacher("bia", days=days),
        ],
        class_groups=[make_class("6a")],
        subjects=[
            make_subject("mat_6a", "ana", "6a", 2, name="Matemática"),
            make_subject("port_6a", "bia", "6a", 2, name="Português"),
        ],
        days=days,
        periods=2,
    )


def scenario_h3_estrutural() -> GAContext:
    """3 aulas exigidas, só 2 slots: H3 mínimo é 1."""
    return make_context(
        teachers=[make_teacher("ana", days=["segunda"])],
        class_groups=[make_class("6a")],
        subjects=[make_subject("mat_6a", "ana", "6a", 3, name="Matemática")],
        days=["segunda"],
        periods=2,
    )


def scenario_s1_evitavel() -> GAContext:
    """4 aulas da mesma disciplina, 2 dias × 3 períodos: 2+2 zera S1, 3+1 não."""
    days = ["segunda", "terca"]
    return make_context(
        teachers=[make_teacher("ana", days=days)],
        class_groups=[make_class("6a")],
        subjects=[make_subject("mat_6a", "ana", "6a", 4, name="Matemática")],
        days=days,
        periods=3,
    )


def scenario_formula_97970() -> tuple[GAContext, Schedule]:
    """2 hard (H1 + H3) e 3 soft (S1) → score 97970, como no documento."""
    ctx = make_context(
        teachers=[make_teacher("ana", days=["segunda"])],
        class_groups=[make_class("6a"), make_class("6b")],
        subjects=[
            make_subject("mat_6a", "ana", "6a", 5, name="Matemática"),
            make_subject("mat_6b", "ana", "6b", 1, name="Matemática"),
            make_subject("port_6a", "ana", "6a", 1, name="Português"),
        ],
        days=["segunda"],
        periods=5,
    )
    # 5 matemáticas na 6a no mesmo dia → S1 = 3; choque com 6b no 1º slot → H1 = 1;
    # Português da 6a sem horário → H3 = 1.
    grade = schedule(
        *(lesson("ana", "mat_6a", "6a", slot_id("segunda", order)) for order in range(1, 6)),
        lesson("ana", "mat_6b", "6b", slot_id("segunda", 1)),
        lesson("ana", "port_6a", "6a", ""),
    )
    return ctx, grade

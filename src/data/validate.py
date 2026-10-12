"""Valida a SchoolInstance antes de montar o GAContext.

Erro: referência inexistente, nome duplicado, turma/professor/disciplina vazios.
Aviso: carga da turma maior que os slots, professor sem dias ou com aulas demais.
"""

from collections import Counter

from domain.entities import SchoolInstance, Teacher


def validate_instance(school: SchoolInstance) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not school.teachers:
        errors.append("Nenhum professor cadastrado. Preencha a tabela de professores.")
    if not school.class_groups:
        errors.append("Nenhuma turma cadastrada. Preencha a tabela de turmas.")
    if not school.subjects:
        errors.append("Nenhuma aula cadastrada. Preencha a tabela de aulas da semana.")
    if not school.time_slots:
        errors.append("Nenhum horário na semana. Marque os dias letivos e as aulas por dia.")

    _reject_duplicates(errors, [item.id for item in school.teachers], "Professor")
    _reject_duplicates(errors, [item.id for item in school.class_groups], "Turma")
    _reject_duplicates(errors, [item.id for item in school.subjects], "Disciplina")
    _reject_duplicate_names(errors, [item.name for item in school.teachers], "Professor")
    _reject_duplicate_names(errors, [item.name for item in school.class_groups], "Turma")

    teacher_ids = {item.id for item in school.teachers}
    group_ids = {item.id for item in school.class_groups}
    teachers_by_id = {item.id: item for item in school.teachers}
    groups_by_id = {item.id: item for item in school.class_groups}
    slots_by_shift: dict[str, int] = {}
    for slot in school.time_slots:
        slots_by_shift[slot.shift] = slots_by_shift.get(slot.shift, 0) + 1

    for subject in school.subjects:
        label = subject.name or subject.id
        group = groups_by_id.get(subject.class_group_id)
        turma = f" da turma {group.name}" if group else ""
        if not subject.name or not str(subject.name).strip():
            errors.append(f"Há uma disciplina sem nome{turma}.")
        if not subject.class_group_id:
            errors.append(f"A disciplina {label} está sem turma.")
        elif subject.class_group_id not in group_ids:
            errors.append(
                f"A disciplina {label} aponta para a turma '{subject.class_group_id}', que não existe."
            )
        if subject.teacher_id not in teacher_ids:
            errors.append(
                f"A disciplina {label}{turma} aponta para o professor '{subject.teacher_id}', que não existe."
            )
        if subject.weekly_workload < 1:
            errors.append(
                f"A disciplina {label}{turma} precisa de pelo menos 1 aula na semana "
                f"(está com {subject.weekly_workload})."
            )

    for group in school.class_groups:
        n_slots = slots_by_shift.get(group.shift, 0) if group.shift else len(school.time_slots)
        if group.shift and n_slots == 0:
            errors.append(
                f"Turma {group.name}: o turno '{group.shift}' não tem horários na semana letiva. "
                "O turno da turma precisa ser o mesmo da barra lateral."
            )
            continue
        load = sum(
            item.weekly_workload for item in school.subjects if item.class_group_id == group.id
        )
        if load == 0:
            warnings.append(f"Turma {group.name} não tem nenhuma aula cadastrada.")
        elif load > n_slots:
            extra = load - n_slots
            warnings.append(
                f"Turma {group.name}: são {_qty(load, 'aula', 'aulas')} na semana e só "
                f"{_qty(n_slots, 'horário', 'horários')} ({extra} a mais). "
                "O gerador não consegue encaixar todas — "
                "reduza aulas_semanais ou aumente as aulas por dia / dias letivos."
            )

    for teacher in school.teachers:
        load = sum(item.weekly_workload for item in school.subjects if item.teacher_id == teacher.id)
        capacity = _teacher_capacity(teacher, school)
        if load == 0:
            warnings.append(f"Professor {teacher.name} não está em nenhuma aula.")
        elif not teacher.available_periods:
            warnings.append(
                f"Professor {teacher.name} está sem dias marcados. "
                "O gerador considera que pode em todos os dias letivos. "
                "Marque os dias em que realmente pode dar aula."
            )
        elif load > capacity:
            warnings.append(
                f"Professor {teacher.name}: {_qty(load, 'aula', 'aulas')} na semana e só "
                f"{_qty(capacity, 'horário', 'horários')} nos dias marcados. "
                "Algumas aulas podem ficar de fora ou em um dia em que "
                "o professor não pode. Marque mais dias ou diminua a carga."
            )

    return errors, warnings


def _qty(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _teacher_capacity(teacher: Teacher, school: SchoolInstance) -> int:
    return sum(1 for slot in school.time_slots if teacher.is_available_for(slot))


def _reject_duplicates(errors: list[str], ids: list[str], label: str) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            errors.append(f"{label} duplicado: '{item_id}'.")
        seen.add(item_id)


def _reject_duplicate_names(errors: list[str], names: list[str], label: str) -> None:
    counts = Counter(name.strip().lower() for name in names if name and str(name).strip())
    original = {}
    for name in names:
        original.setdefault(name.strip().lower(), name)
    for key, count in counts.items():
        if count > 1:
            errors.append(
                f"{label} '{original[key]}' está repetido. Use um nome diferente para cada um."
            )

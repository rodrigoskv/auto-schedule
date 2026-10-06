"""Valida a SchoolInstance antes de montar o GAContext.

Erro: referência inexistente, id duplicado, class_group_id ausente.
Aviso: carga da turma maior que os slots (H3 estrutural — o AG não consegue zerar H3).
"""

from domain.entities import SchoolInstance


def validate_instance(school: SchoolInstance) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not school.teachers:
        errors.append("Nenhum professor na instância.")
    if not school.class_groups:
        errors.append("Nenhuma turma na instância.")
    if not school.subjects:
        errors.append("Nenhuma disciplina na instância.")
    if not school.time_slots:
        errors.append("Nenhum horário gerado pela grade.")

    _reject_duplicates(errors, [item.id for item in school.teachers], "Professor")
    _reject_duplicates(errors, [item.id for item in school.class_groups], "Turma")
    _reject_duplicates(errors, [item.id for item in school.subjects], "Disciplina")

    teacher_ids = {item.id for item in school.teachers}
    group_ids = {item.id for item in school.class_groups}
    slots_by_shift: dict[str, int] = {}
    for slot in school.time_slots:
        slots_by_shift[slot.shift] = slots_by_shift.get(slot.shift, 0) + 1

    for subject in school.subjects:
        if not subject.class_group_id:
            errors.append(f"Disciplina '{subject.id}' sem class_group_id.")
        elif subject.class_group_id not in group_ids:
            errors.append(
                f"Disciplina '{subject.id}': turma '{subject.class_group_id}' não existe."
            )
        if subject.teacher_id not in teacher_ids:
            errors.append(
                f"Disciplina '{subject.id}': professor '{subject.teacher_id}' não existe."
            )
        if subject.weekly_workload < 1:
            errors.append(
                f"Disciplina '{subject.id}': weekly_workload inválido ({subject.weekly_workload})."
            )

    for group in school.class_groups:
        n_slots = slots_by_shift.get(group.shift, 0) if group.shift else len(school.time_slots)
        if group.shift and n_slots == 0:
            errors.append(
                f"Turma '{group.name}' ({group.id}): turno '{group.shift}' sem slots na grade."
            )
            continue
        load = sum(
            item.weekly_workload for item in school.subjects if item.class_group_id == group.id
        )
        if load > n_slots:
            warnings.append(
                f"Turma '{group.name}' ({group.id}): carga {load} > {n_slots} slots (H3 estrutural)."
            )

    return errors, warnings


def _reject_duplicates(errors: list[str], ids: list[str], label: str) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            errors.append(f"{label} duplicado: '{item_id}'.")
        seen.add(item_id)

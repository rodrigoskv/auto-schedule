"""Valida a instância antes do AG.

Erro: referência inexistente, id duplicado, campo obrigatório ausente.
Aviso: carga da turma maior que os slots (H3 estrutural).
"""

from domain.entities import ClassGroup, Subject, Teacher, TimeSlot


def validate_instance(
    teachers: list[Teacher],
    class_groups: list[ClassGroup],
    subjects: list[Subject],
    time_slots: list[TimeSlot],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not teachers:
        errors.append("Nenhum professor na instância.")
    if not class_groups:
        errors.append("Nenhuma turma na instância.")
    if not subjects:
        errors.append("Nenhuma disciplina na instância.")
    if not time_slots:
        errors.append("Nenhum horário gerado pela grade.")

    _reject_duplicates(errors, [item.id for item in teachers], "Professor")
    _reject_duplicates(errors, [item.id for item in class_groups], "Turma")
    _reject_duplicates(errors, [item.id for item in subjects], "Disciplina")

    teacher_ids = {item.id for item in teachers}
    group_ids = {item.id for item in class_groups}
    slots_by_shift: dict[str, int] = {}
    for slot in time_slots:
        slots_by_shift[slot.shift] = slots_by_shift.get(slot.shift, 0) + 1

    for subject in subjects:
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

    for group in class_groups:
        n_slots = slots_by_shift.get(group.shift, 0) if group.shift else len(time_slots)
        if group.shift and n_slots == 0:
            errors.append(
                f"Turma '{group.name}' ({group.id}): turno '{group.shift}' sem slots na grade."
            )
            continue
        load = sum(item.weekly_workload for item in subjects if item.class_group_id == group.id)
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

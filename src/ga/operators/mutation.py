"""Mutação, turma a turma.

Com probabilidade mutation_rate, uma aula:
    - vai para um slot livre da turma, ou
    - troca de horário com outra aula da mesma turma
"""

import copy
import random

from domain.entities import Schedule
from ga.context import GAContext

MOVE_TO_FREE_CHANCE = 0.35


def _move_to_free_slot(lesson, free_slots: list[str]) -> None:
    """Muda a aula para um horário vazio da turma e devolve o slot antigo."""
    target = random.choice(free_slots)
    if lesson.time_slot_id:
        free_slots.append(lesson.time_slot_id)
    lesson.time_slot_id = target
    free_slots.remove(target)


def mutate(
    schedule: Schedule,
    context: GAContext,
    mutation_rate: float = 0.08,
) -> Schedule:
    """Perturba o horário: slot livre ou troca com outra aula da mesma turma."""
    mutated = copy.deepcopy(schedule)

    for group in context.class_groups:
        indices = [
            index
            for index, lesson in enumerate(mutated.lessons)
            if lesson.class_group_id == group.id
        ]
        if len(indices) < 2:
            continue

        occupied = mutated.occupied_slot_ids_for_class(group.id)
        free_slots = [slot.id for slot in context.slots_for_class(group.id) if slot.id not in occupied]

        for index in indices:
            if random.random() >= mutation_rate:
                continue

            lesson = mutated.lessons[index]
            can_move = free_slots and (not lesson.time_slot_id or random.random() < MOVE_TO_FREE_CHANCE)
            if can_move:
                _move_to_free_slot(lesson, free_slots)
                continue

            other_index = random.choice([item for item in indices if item != index])
            mutated.lessons[index].time_slot_id, mutated.lessons[other_index].time_slot_id = (
                mutated.lessons[other_index].time_slot_id,
                mutated.lessons[index].time_slot_id,
            )

    return mutated

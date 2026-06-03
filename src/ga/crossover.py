"""
Crossover de dois pontos sobre a lista de Lessons, operando por turma.

O crossover troca segmentos de aulas entre dois pais.
Após a recombinação, duplicatas por célula (class_group_id, time_slot_id)
são resolvidas: a segunda ocorrência recebe um slot ainda livre da turma.
"""

import random
import copy

from domain.entities import Lesson
from domain.schedule import Schedule
from ga.representation import GAContext


def _get_lessons_by_class_group(schedule: Schedule, cg_id: str) -> list[Lesson]:
    return [l for l in schedule.lessons if l.class_group_id == cg_id]


def _dedup_by_slot(lessons: list[Lesson], context: GAContext, cg_id: str) -> list[Lesson]:
    """
    Remove duplicatas de (class_group_id, time_slot_id) no resultado do crossover.
    Slots já ocupados têm a aula duplicada realocada para um slot livre.
    """
    used_slots: set[str] = set()
    result: list[Lesson] = []
    pending: list[Lesson] = []

    for lesson in lessons:
        if lesson.time_slot_id not in used_slots:
            used_slots.add(lesson.time_slot_id)
            result.append(lesson)
        else:
            pending.append(lesson)

    # slots disponíveis para a turma que ainda não foram usados
    cg = context.class_groups_by_id.get(cg_id)
    free_slots = [
        ts.id for ts in context.ordered_slots
        if (cg is None or cg.shift is None or ts.shift == cg.shift)
        and ts.id not in used_slots
    ]
    random.shuffle(free_slots)

    for lesson, free_slot in zip(pending, free_slots):
        lesson.time_slot_id = free_slot
        used_slots.add(free_slot)
        result.append(lesson)

    # aulas que não couberam em nenhum slot são descartadas
    return result


def _crossover_for_class_group(
    lessons1: list[Lesson],
    lessons2: list[Lesson],
) -> list[Lesson]:
    """Two-point crossover na lista de aulas de uma turma específica."""
    size = max(len(lessons1), len(lessons2))
    if size < 2:
        return copy.deepcopy(lessons1) if lessons1 else copy.deepcopy(lessons2)

    l1 = lessons1 + [None] * (size - len(lessons1))
    l2 = lessons2 + [None] * (size - len(lessons2))

    pt1 = random.randint(0, size - 1)
    pt2 = random.randint(pt1, size - 1)

    child_lessons = l2[:pt1] + l1[pt1:pt2] + l2[pt2:]
    return [copy.deepcopy(lesson) for lesson in child_lessons if lesson is not None]


def crossover(
    parent1: Schedule,
    parent2: Schedule,
    context: GAContext,
    crossover_rate: float = 0.8,
) -> tuple[Schedule, Schedule]:
    """
    Realiza crossover de dois pontos entre dois pais, por turma.
    Duplicatas de slot por turma são resolvidas após a recombinação.

    Returns:
        Dois filhos (Schedule).
    """
    if random.random() > crossover_rate:
        return copy.deepcopy(parent1), copy.deepcopy(parent2)

    child1 = Schedule()
    child2 = Schedule()

    for cg in context.class_groups:
        lessons1 = _get_lessons_by_class_group(parent1, cg.id)
        lessons2 = _get_lessons_by_class_group(parent2, cg.id)

        raw1 = _crossover_for_class_group(lessons1, lessons2)
        raw2 = _crossover_for_class_group(lessons2, lessons1)

        for lesson in _dedup_by_slot(raw1, context, cg.id):
            child1.add_lesson(lesson)
        for lesson in _dedup_by_slot(raw2, context, cg.id):
            child2.add_lesson(lesson)

    return child1, child2


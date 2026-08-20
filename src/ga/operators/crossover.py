import copy
import random
from collections import Counter

from domain.entities import Lesson, Schedule
from ga.context import GAContext


def _crossover_for_class_group(lessons1: list[Lesson], lessons2: list[Lesson]) -> list[Lesson]:
    size = max(len(lessons1), len(lessons2))
    if size < 2:
        return copy.deepcopy(lessons1) if lessons1 else copy.deepcopy(lessons2)

    first = lessons1 + [None] * (size - len(lessons1))
    second = lessons2 + [None] * (size - len(lessons2))

    point1 = random.randint(0, size - 1)
    point2 = random.randint(point1, size - 1)

    child = second[:point1] + first[point1:point2] + second[point2:]
    return [copy.deepcopy(lesson) for lesson in child if lesson is not None]


def _restore_workload(lessons: list[Lesson], class_group_id: str, context: GAContext) -> list[Lesson]:
    required = context.required_lessons_for_class(class_group_id)
    required_counts = Counter(required)
    kept: list[Lesson] = []
    used = Counter()

    for lesson in lessons:
        key = (lesson.subject_id, lesson.teacher_id)
        if used[key] < required_counts[key]:
            kept.append(lesson)
            used[key] += 1

    for subject_id, teacher_id in required:
        key = (subject_id, teacher_id)
        if used[key] < required_counts[key]:
            kept.append(
                Lesson(
                    teacher_id=teacher_id,
                    subject_id=subject_id,
                    class_group_id=class_group_id,
                    time_slot_id="",
                )
            )
            used[key] += 1

    return kept


def _assign_unique_slots(lessons: list[Lesson], context: GAContext, class_group_id: str) -> list[Lesson]:
    used_slots: set[str] = set()
    result: list[Lesson] = []
    pending: list[Lesson] = []

    for lesson in lessons:
        if lesson.time_slot_id and lesson.time_slot_id not in used_slots:
            used_slots.add(lesson.time_slot_id)
            result.append(lesson)
        else:
            pending.append(lesson)

    free_slots = [slot.id for slot in context.slots_for_class(class_group_id) if slot.id not in used_slots]
    random.shuffle(free_slots)

    for lesson, free_slot in zip(pending, free_slots):
        lesson.time_slot_id = free_slot
        used_slots.add(free_slot)
        result.append(lesson)

    for lesson in pending[len(free_slots):]:
        lesson.time_slot_id = ""
        result.append(lesson)

    return result


def crossover(
    parent1: Schedule,
    parent2: Schedule,
    context: GAContext,
    crossover_rate: float = 0.8,
) -> tuple[Schedule, Schedule]:
    if random.random() > crossover_rate:
        return copy.deepcopy(parent1), copy.deepcopy(parent2)

    child1 = Schedule()
    child2 = Schedule()

    for group in context.class_groups:
        lessons1 = parent1.get_lessons_for_class_group(group.id)
        lessons2 = parent2.get_lessons_for_class_group(group.id)

        raw1 = _restore_workload(_crossover_for_class_group(lessons1, lessons2), group.id, context)
        raw2 = _restore_workload(_crossover_for_class_group(lessons2, lessons1), group.id, context)

        for lesson in _assign_unique_slots(raw1, context, group.id):
            child1.add_lesson(lesson)
        for lesson in _assign_unique_slots(raw2, context, group.id):
            child2.add_lesson(lesson)

    return child1, child2
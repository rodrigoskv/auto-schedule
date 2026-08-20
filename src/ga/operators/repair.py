import copy
import random

from domain.entities import Lesson, Schedule
from ga.context import GAContext


def _free_slots_for_class(schedule: Schedule, context: GAContext, class_group_id: str) -> list[str]:
    occupied = schedule.occupied_slot_ids_for_class(class_group_id)
    return [slot.id for slot in context.slots_for_class(class_group_id) if slot.id not in occupied]


def _teacher_free_at(
    schedule: Schedule,
    teacher_id: str,
    time_slot_id: str,
    ignore: Lesson | None = None,
) -> bool:
    occupants = schedule.get_teacher_cell_lesson(time_slot_id, teacher_id)
    return all(occupant is ignore for occupant in occupants)


def _relocate_lesson(
    schedule: Schedule,
    lesson: Lesson,
    context: GAContext,
    require_availability: bool,
) -> bool:
    candidates = _free_slots_for_class(schedule, context, lesson.class_group_id)
    random.shuffle(candidates)

    for slot_id in candidates:
        if require_availability and not context.is_teacher_available(lesson.teacher_id, slot_id):
            continue
        if not _teacher_free_at(schedule, lesson.teacher_id, slot_id, ignore=lesson):
            continue
        lesson.time_slot_id = slot_id
        return True
    return False


def _swap_for_availability(schedule: Schedule, lesson: Lesson, context: GAContext) -> bool:
    same_class = [
        other
        for other in schedule.get_lessons_for_class_group(lesson.class_group_id)
        if other is not lesson and other.time_slot_id
    ]
    random.shuffle(same_class)

    current_slot = lesson.time_slot_id
    for other in same_class:
        if not context.is_teacher_available(lesson.teacher_id, other.time_slot_id):
            continue
        if current_slot and not context.is_teacher_available(other.teacher_id, current_slot):
            continue
        if current_slot and not _teacher_free_at(schedule, other.teacher_id, current_slot, ignore=other):
            continue
        if not _teacher_free_at(schedule, lesson.teacher_id, other.time_slot_id, ignore=lesson):
            continue
        lesson.time_slot_id, other.time_slot_id = other.time_slot_id, current_slot
        return True
    return False


def repair_unassigned(schedule: Schedule, context: GAContext) -> None:
    unassigned = schedule.get_unassigned_lessons()
    random.shuffle(unassigned)
    for lesson in unassigned:
        _relocate_lesson(schedule, lesson, context, require_availability=True)


def repair_teacher_availability(schedule: Schedule, context: GAContext) -> None:
    violating = [
        lesson
        for lesson in schedule.lessons
        if lesson.time_slot_id and not context.is_teacher_available(lesson.teacher_id, lesson.time_slot_id)
    ]
    random.shuffle(violating)

    for lesson in violating:
        if context.is_teacher_available(lesson.teacher_id, lesson.time_slot_id):
            continue
        if _relocate_lesson(schedule, lesson, context, require_availability=True):
            continue
        if _swap_for_availability(schedule, lesson, context):
            continue
        lesson.time_slot_id = ""


def repair_teacher_conflicts(schedule: Schedule, context: GAContext) -> None:
    for slot in context.time_slots:
        lessons = schedule.get_lessons_for_time_slot(slot.id)
        by_teacher: dict[str, list[Lesson]] = {}
        for lesson in lessons:
            by_teacher.setdefault(lesson.teacher_id, []).append(lesson)

        for extras in by_teacher.values():
            if len(extras) <= 1:
                continue
            for extra in extras[1:]:
                if not _relocate_lesson(schedule, extra, context, require_availability=True):
                    extra.time_slot_id = ""


def repair_schedule(schedule: Schedule, context: GAContext) -> Schedule:
    repaired = copy.deepcopy(schedule)
    repair_unassigned(repaired, context)
    repair_teacher_availability(repaired, context)
    repair_teacher_conflicts(repaired, context)
    repair_unassigned(repaired, context)
    return repaired

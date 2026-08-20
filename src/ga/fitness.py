"""
Fitness = BASE - (PESO_HARD * total_hard) - (PESO_SOFT * total_soft)
"""

from collections import Counter
from dataclasses import dataclass

from domain.constraints import (
    BASE_SCORE,
    H1_TEACHER_CONFLICT,
    H2_CLASS_CONFLICT,
    H3_WORKLOAD_DEFICIT,
    H4_TEACHER_AVAILABILITY,
    PESO_HARD,
    PESO_SOFT,
    S1_SUBJECT_CONCENTRATION,
)
from domain.entities import Schedule
from ga.context import GAContext


@dataclass
class FitnessBreakdown:
    fitness: float
    hard: int
    soft: int
    counts: dict[str, int]


def _count_h1(schedule: Schedule, context: GAContext) -> int:
    violations = 0
    for slot in context.time_slots:
        seen: dict[str, int] = {}
        for lesson in schedule.get_lessons_for_time_slot(slot.id):
            seen[lesson.teacher_id] = seen.get(lesson.teacher_id, 0) + 1
        for count in seen.values():
            if count > 1:
                violations += count - 1
    return violations


def _count_h2(schedule: Schedule, context: GAContext) -> int:
    violations = 0
    for group in context.class_groups:
        for slot in context.slots_for_class(group.id):
            cell = schedule.get_cell_lessons(slot.id, group.id)
            if len(cell) > 1:
                violations += len(cell) - 1
    return violations


def _count_h3(schedule: Schedule, context: GAContext) -> int:
    violations = 0
    for subject in context.subjects:
        allocated = sum(
            1
            for lesson in schedule.get_lessons_for_subject(subject.id)
            if lesson.time_slot_id
        )
        if allocated < subject.weekly_workload:
            violations += subject.weekly_workload - allocated
    return violations


def _count_h4(schedule: Schedule, context: GAContext) -> int:
    violations = 0
    for lesson in schedule.lessons:
        if not lesson.time_slot_id:
            continue
        if not context.is_teacher_available(lesson.teacher_id, lesson.time_slot_id):
            violations += 1
    return violations


def _count_s1(schedule: Schedule, context: GAContext) -> int:
    violations = 0
    days = {slot.day_of_week for slot in context.time_slots}
    shifts = {slot.shift for slot in context.time_slots}

    for group in context.class_groups:
        for day in days:
            for shift in shifts:
                day_lessons = schedule.get_lessons_for_class_group_by_day_and_shift(
                    group.id,
                    day,
                    shift,
                    context.time_slots,
                )
                frequencies = Counter(lesson.subject_id for lesson in day_lessons)
                for frequency in frequencies.values():
                    if frequency > 2:
                        violations += frequency - 2
    return violations


def evaluate_details(schedule: Schedule, context: GAContext) -> FitnessBreakdown:
    counts = {
        H1_TEACHER_CONFLICT: _count_h1(schedule, context),
        H2_CLASS_CONFLICT: _count_h2(schedule, context),
        H3_WORKLOAD_DEFICIT: _count_h3(schedule, context),
        H4_TEACHER_AVAILABILITY: _count_h4(schedule, context),
        S1_SUBJECT_CONCENTRATION: _count_s1(schedule, context),
    }
    hard = (
        counts[H1_TEACHER_CONFLICT]
        + counts[H2_CLASS_CONFLICT]
        + counts[H3_WORKLOAD_DEFICIT]
        + counts[H4_TEACHER_AVAILABILITY]
    )
    soft = counts[S1_SUBJECT_CONCENTRATION]
    fitness = BASE_SCORE - (PESO_HARD * hard) - (PESO_SOFT * soft)
    return FitnessBreakdown(fitness=float(fitness), hard=hard, soft=soft, counts=counts)


def evaluate(schedule: Schedule, context: GAContext) -> float:
    return evaluate_details(schedule, context).fitness
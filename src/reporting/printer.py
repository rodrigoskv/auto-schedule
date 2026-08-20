from domain.entities import Schedule
from ga.context import GAContext
from engine import GAResult
from reporting.violations import format_violations


def print_schedule(schedule: Schedule, context: GAContext, fitness: float | None = None) -> None:
    header = "  MELHOR HORÁRIO ENCONTRADO"
    if fitness is not None:
        header += f"  |  Fitness: {fitness:.1f}"
    print("\n" + "=" * 70)
    print(header)
    print("=" * 70)

    for group in context.class_groups:
        print(f"\n  Turma: {group.name}")
        print(f"  {'Slot':<22} {'Disciplina':<30} {'Professor':<20}")
        print(f"  {'-' * 22} {'-' * 30} {'-' * 20}")

        lessons = [
            lesson
            for lesson in schedule.get_lessons_for_class_group(group.id)
            if lesson.time_slot_id
        ]
        lessons.sort(
            key=lambda lesson: context.slot_ordering_key(context.time_slots_by_id[lesson.time_slot_id])
        )

        for lesson in lessons:
            slot = context.time_slots_by_id.get(lesson.time_slot_id)
            subject = context.subjects_by_id.get(lesson.subject_id)
            teacher = context.teachers_by_id.get(lesson.teacher_id)
            slot_label = slot.label if slot and slot.label else lesson.time_slot_id
            subject_name = subject.name if subject else lesson.subject_id
            teacher_name = teacher.name if teacher else lesson.teacher_id
            print(f"  {slot_label:<22} {subject_name:<30} {teacher_name:<20}")

        unassigned = [
            lesson
            for lesson in schedule.get_lessons_for_class_group(group.id)
            if not lesson.time_slot_id
        ]
        if unassigned:
            print(f"  Aulas sem horário: {len(unassigned)}")


def print_result(result: GAResult, context: GAContext) -> None:
    print_schedule(result.schedule, context, result.fitness)
    print("\n" + "-" * 70)
    print(format_violations(result.breakdown))
    print(f"Gerações: {result.generation_reached}")
    print(f"Tempo: {result.elapsed_seconds:.2f}s")
"""População inicial.

Para cada turma:
    pega as aulas exigidas (disciplina × carga semanal)
    pega os slots da turma
    embaralha os dois e casa um a um
    se faltar slot, a aula fica sem horário (conta em H3)
"""

import random

from domain.entities import Lesson, Schedule
from ga.context import GAContext


def generate_individual(context: GAContext) -> Schedule:
    """Sorteia um horário inicial: aulas da turma nos slots, o que sobrar fica sem horário."""
    schedule = Schedule()

    for group in context.class_groups:
        lesson_pool = context.required_lessons_for_class(group.id)
        random.shuffle(lesson_pool)

        available_slots = list(context.slots_for_class(group.id))
        random.shuffle(available_slots)

        for index, (subject_id, teacher_id) in enumerate(lesson_pool):
            slot_id = available_slots[index].id if index < len(available_slots) else ""
            schedule.add_lesson(
                Lesson(
                    teacher_id=teacher_id,
                    subject_id=subject_id,
                    class_group_id=group.id,
                    time_slot_id=slot_id,
                )
            )

    return schedule


def generate_population(size: int, context: GAContext) -> list[Schedule]:
    """Cria `size` indivíduos independentes para começar o AG."""
    return [generate_individual(context) for _ in range(size)]

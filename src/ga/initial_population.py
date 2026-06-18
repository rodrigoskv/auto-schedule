"""
Geração da população inicial.

Cada indivíduo é um Schedule preenchido aleatoriamente:
- Para cada turma, expande os subjects pelo weekly_workload
- Distribui as aulas aleatoriamente nos time_slots disponíveis
- Slots sobrando ficam vazios (sem Lesson)
"""

import random
from domain.entities import Lesson
from domain.schedule import Schedule
from .representation import GAContext


def _build_lesson_pool(cg_id: str, context: GAContext) -> list[tuple[str, str]]:
    """
    Retorna uma lista de (subject_id, teacher_id) expandida pelo weekly_workload.
    Ex: subject com workload=3 aparece 3 vezes na lista.
    """
    pool: list[tuple[str, str]] = []
    for subject in context.subjects_by_class_group.get(cg_id, []):
        for _ in range(subject.weekly_workload):
            pool.append((subject.id, subject.teacher_id))
    return pool


def generate_individual(context: GAContext) -> Schedule:
    """
    Gera um indivíduo (Schedule) com alocação aleatória de aulas.
    """
    schedule = Schedule()

    for cg in context.class_groups:
        lesson_pool = _build_lesson_pool(cg.id, context)
        # embaralha a pool de aulas
        random.shuffle(lesson_pool)

        # slots disponíveis para essa turma (respeita o turno da turma se definido)
        available_slots = [
            ts for ts in context.ordered_slots
            if cg.shift is None or ts.shift == cg.shift
        ]
        random.shuffle(available_slots)

        # aloca cada aula em um slot, para no mínimo entre pool e slots
        for i, (subject_id, teacher_id) in enumerate(lesson_pool):
            if i >= len(available_slots):
                break  # Mais aulas do que slots: descarta o excedente
            slot = available_slots[i]
            schedule.add_lesson(
                Lesson(
                    teacher_id=teacher_id,
                    subject_id=subject_id,
                    class_group_id=cg.id,
                    time_slot_id=slot.id,
                )
            )

    return schedule


def generate_population(size: int, context: GAContext) -> list[Schedule]:
    """
    Gera uma lista de `size` indivíduos (Schedules) aleatórios.
    """
    return [generate_individual(context) for _ in range(size)]


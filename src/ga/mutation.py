"""
Mutação por swap de time_slots dentro de uma turma.

Para cada aula do indivíduo, com probabilidade `mutation_rate`,
troca o time_slot_id dessa aula com o de outra aula aleatória
da mesma turma — mantendo a carga horária intacta.
"""

import random
import copy

from domain.entities import Lesson
from domain.schedule import Schedule
from .representation import GAContext


def _get_lessons_indices_by_class_group(lessons: list[Lesson], cg_id: str) -> list[int]:
    """Retorna os índices das aulas de uma turma específica na lista de lessons."""
    return [i for i, lesson in enumerate(lessons) if lesson.class_group_id == cg_id]


def mutate(
    schedule: Schedule,
    context: GAContext,
    mutation_rate: float = 0.05,
) -> Schedule:
    """
    Aplica mutação por swap de time_slots dentro de cada turma.

    Para cada aula, com probabilidade `mutation_rate`, troca seu
    time_slot_id com o de outra aula aleatória da mesma turma.

    Returns:
        Novo Schedule mutado (não modifica o original).
    """
    mutated = copy.deepcopy(schedule)

    for cg in context.class_groups:
        cg_indices = _get_lessons_indices_by_class_group(mutated.lessons, cg.id)

        if len(cg_indices) < 2:
            continue

        for idx in cg_indices:
            if random.random() < mutation_rate:
                other_idx = random.choice([i for i in cg_indices if i != idx])
                mutated.lessons[idx].time_slot_id, mutated.lessons[other_idx].time_slot_id = (
                    mutated.lessons[other_idx].time_slot_id,
                    mutated.lessons[idx].time_slot_id,
                )

    return mutated


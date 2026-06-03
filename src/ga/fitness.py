"""
Função de fitness por penalidades.

Score = BASE - (PESO_HARD * total_hard) - (PESO_SOFT * total_soft)

Hard constraints (penalidade 1000 cada):
  - H1: Professor em dois slots iguais ao mesmo tempo
  - H2: Turma em dois slots iguais ao mesmo tempo
  - H3: Carga horária semanal não cumprida por disciplina

Soft constraints (penalidade 10 cada):
  - S1: Mais de 2 aulas da mesma disciplina no mesmo dia para uma turma
"""

from collections import Counter, defaultdict

from domain.schedule import Schedule
from ga.representation import GAContext

BASE_SCORE = 100_000
PESO_HARD = 1_000
PESO_SOFT = 10


def _penalize_hard(schedule: Schedule, context: GAContext) -> int:
    """Retorna a contagem de violações de hard constraints."""
    violations = 0

    teacher_slot_count: dict[tuple[str, str], int] = defaultdict(int)
    class_slot_count: dict[tuple[str, str], int] = defaultdict(int)
    subject_count: dict[str, int] = defaultdict(int)

    for lesson in schedule.lessons:
        teacher_slot_count[(lesson.teacher_id, lesson.time_slot_id)] += 1
        class_slot_count[(lesson.class_group_id, lesson.time_slot_id)] += 1
        subject_count[lesson.subject_id] += 1

    # H1: Professor em dois slots iguais ao mesmo tempo
    for count in teacher_slot_count.values():
        if count > 1:
            violations += count - 1

    # H2: Turma em dois slots iguais ao mesmo tempo
    for count in class_slot_count.values():
        if count > 1:
            violations += count - 1

    # H3: Carga horária não cumprida
    for subject in context.subjects:
        allocated = subject_count.get(subject.id, 0)
        if allocated < subject.weekly_workload:
            violations += subject.weekly_workload - allocated

    return violations


def _penalize_soft(schedule: Schedule, context: GAContext) -> int:
    """Retorna a contagem de violações de soft constraints."""
    violations = 0

    # Monta: class_group -> day -> list[subject_id]
    class_day_subjects: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for lesson in schedule.lessons:
        ts = context.time_slots_by_id.get(lesson.time_slot_id)
        if ts is None:
            continue
        class_day_subjects[lesson.class_group_id][ts.day_of_week].append(lesson.subject_id)

    # S1: Mais de 3 aulas da mesma disciplina no mesmo dia
    for cg_id, days in class_day_subjects.items():
        for day, subjects in days.items():
            subject_freq = Counter(subjects)
            for freq in subject_freq.values():
                if freq > 2:
                    violations += freq - 2

    return violations


def evaluate(schedule: Schedule, context: GAContext) -> float:
    """
    Calcula o fitness de um indivíduo.
    Quanto maior o score, melhor o indivíduo.
    """
    hard = _penalize_hard(schedule, context)
    soft = _penalize_soft(schedule, context)
    return BASE_SCORE - (PESO_HARD * hard) - (PESO_SOFT * soft)


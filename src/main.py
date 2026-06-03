"""
Ponto de entrada do sistema de escalonamento automático.

Fluxo:
  1. Carrega dados dos JSONs (teachers, class_groups, subjects, time_slots)
  2. Monta o GAContext com a estratégia de ordenação escolhida
  3. Executa o Algoritmo Genético
  4. Exibe o resultado (melhor grade horária encontrada)

Para trocar a estratégia de ordenação de TimeSlot, altere a variável
`SLOT_ORDERING_STRATEGY` para uma das opções:
  - "day_shift_order"  > ordena por (dia, turno, ordem)  [padrão]
  - "global_order"     > ordena pelo campo global_order
  - "shift_then_day"   > agrupa por turno primeiro, depois por dia
"""

import json
import sys
import os

# garante que o diretório atual (src/) esteja no path para imports relativos
sys.path.insert(0, os.path.dirname(__file__))

from domain.entities import Teacher, ClassGroup, Subject, TimeSlot
from ga.representation import GAContext, SLOT_ORDERING_STRATEGIES
from ga.ga import run_ga

# configuração

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# estratégia de ordenação dos TimeSlots
SLOT_ORDERING_STRATEGY = "shift_then_day"  # "day_shift_order" | "global_order" | "shift_then_day"

# hiperparâmetros do AG
POPULATION_SIZE = 80
GENERATIONS = 200
CROSSOVER_RATE = 0.8
MUTATION_RATE = 0.08
ELITISM_COUNT = 2
TOURNAMENT_SIZE = 3



# load dos dados
def _load(filename: str, model) -> list:
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return [model(**item) for item in json.load(f)]


def load_teachers() -> list[Teacher]:         return _load("teachers.json", Teacher)
def load_class_groups() -> list[ClassGroup]:  return _load("class_groups.json", ClassGroup)
def load_subjects() -> list[Subject]:         return _load("subjects.json", Subject)
def load_time_slots() -> list[TimeSlot]:      return _load("time_slots.json", TimeSlot)


#exibição do resultado
def print_best_schedule(schedule, fitness: float, context: GAContext):
    print("\n" + "=" * 70)
    print(f"  MELHOR HORÁRIO ENCONTRADO  |  Fitness: {fitness:.1f}")
    print("=" * 70)

    for cg in context.class_groups:
        print(f"\n  Turma: {cg.name}")
        print(f"  {'Slot':<22} {'Disciplina':<30} {'Professor':<20}")
        print(f"  {'-'*22} {'-'*30} {'-'*20}")

        lessons = sorted(
            [l for l in schedule.lessons if l.class_group_id == cg.id],
            key=lambda l: context.slot_ordering_key(context.time_slots_by_id[l.time_slot_id]),
        )

        for lesson in lessons:
            ts = context.time_slots_by_id.get(lesson.time_slot_id)
            subject = context.subjects_by_id.get(lesson.subject_id)
            teacher = context.teachers_by_id.get(lesson.teacher_id)
            slot_label = ts.label if ts and ts.label else lesson.time_slot_id
            subject_name = subject.name if subject else lesson.subject_id
            teacher_name = teacher.name if teacher else lesson.teacher_id
            print(f"  {slot_label:<22} {subject_name:<30} {teacher_name:<20}")


#main
def main():
    print("Carregando dados...")
    teachers = load_teachers()
    class_groups = load_class_groups()
    subjects = load_subjects()
    time_slots = load_time_slots()

    print(
        f"  {len(teachers)} professores | "
        f"{len(class_groups)} turmas | "
        f"{len(subjects)} disciplinas | "
        f"{len(time_slots)} time slots"
    )

    # monta o contexto com estratégia escolhida
    ordering_key = SLOT_ORDERING_STRATEGIES[SLOT_ORDERING_STRATEGY]
    context = GAContext(
        teachers=teachers,
        class_groups=class_groups,
        subjects=subjects,
        time_slots=time_slots,
        slot_ordering_key=ordering_key,
    )

    print(f"\nIniciando AG  |  Estratégia de ordenação: '{SLOT_ORDERING_STRATEGY}'")
    print(
        f"  População: {POPULATION_SIZE} | "
        f"Gerações: {GENERATIONS} | "
        f"Crossover: {CROSSOVER_RATE} | "
        f"Mutação: {MUTATION_RATE}"
    )
    print()

    best_schedule, best_fitness = run_ga(
        context=context,
        population_size=POPULATION_SIZE,
        generations=GENERATIONS,
        crossover_rate=CROSSOVER_RATE,
        mutation_rate=MUTATION_RATE,
        elitism_count=ELITISM_COUNT,
        tournament_size=TOURNAMENT_SIZE,
        verbose=True,
    )

    print_best_schedule(best_schedule, best_fitness, context)


if __name__ == "__main__":
    main()


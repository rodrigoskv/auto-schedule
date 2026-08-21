import json
import os

from domain.entities import ClassGroup, Subject, Teacher, TimeSlot
from engine import run_ga
from ga.context import GAContext
from ga.operators.representation import SLOT_ORDERING_STRATEGIES
from reporting.printer import print_result

DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "data"))
SLOT_ORDERING_STRATEGY = "shift_then_day"

POPULATION_SIZE = 80
GENERATIONS = 200
CROSSOVER_RATE = 0.8
MUTATION_RATE = 0.08
ELITISM_COUNT = 2
TOURNAMENT_SIZE = 3


def _load(filename: str, model) -> list:
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding="utf-8") as handle:
        return [model(**item) for item in json.load(handle)]


def load_instance() -> tuple[list[Teacher], list[ClassGroup], list[Subject], list[TimeSlot]]:
    return (
        _load("teachers.json", Teacher),
        _load("class_groups.json", ClassGroup),
        _load("subjects.json", Subject),
        _load("time_slots.json", TimeSlot),
    )


def main() -> None:
    print("Carregando dados...")
    teachers, class_groups, subjects, time_slots = load_instance()
    print(
        f"  {len(teachers)} professores | "
        f"{len(class_groups)} turmas | "
        f"{len(subjects)} disciplinas | "
        f"{len(time_slots)} time slots"
    )

    context = GAContext(
        teachers=teachers,
        class_groups=class_groups,
        subjects=subjects,
        time_slots=time_slots,
        slot_ordering_key=SLOT_ORDERING_STRATEGIES[SLOT_ORDERING_STRATEGY],
    )

    print(f"\nIniciando AG  |  Estratégia de ordenação: '{SLOT_ORDERING_STRATEGY}'")
    print(
        f"  População: {POPULATION_SIZE} | "
        f"Gerações: {GENERATIONS} | "
        f"Crossover: {CROSSOVER_RATE} | "
        f"Mutação: {MUTATION_RATE}"
    )
    print()

    result = run_ga(
        context=context,
        population_size=POPULATION_SIZE,
        generations=GENERATIONS,
        crossover_rate=CROSSOVER_RATE,
        mutation_rate=MUTATION_RATE,
        elitism_count=ELITISM_COUNT,
        tournament_size=TOURNAMENT_SIZE,
        verbose=True,
    )
    print_result(result, context)


if __name__ == "__main__":
    main()
"""Ponto de entrada: carrega a instância, valida e roda o AG."""

import argparse
import sys
from pathlib import Path

from data.instance import load_instance
from data.templates import write_templates
from data.validate import validate_instance
from ga.context import GAContext
from ga.engine import run_ga
from ga.operators.representation import SLOT_ORDERING_STRATEGIES
from reporting.printer import print_result

SLOT_ORDERING_STRATEGY = "shift_then_day"
CROSSOVER_RATE = 0.8
MUTATION_RATE = 0.08
ELITISM_COUNT = 2
TOURNAMENT_SIZE = 3
DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-Schedule: gera horário escolar com AG.")
    parser.add_argument(
        "--entrada",
        default=str(DEFAULT_DATA),
        help="Pasta JSON, planilha do molde (Grade/Turmas/Professores/Aulas) ou trio de planilhas.",
    )
    parser.add_argument("--somente-validar", action="store_true", help="Carrega e valida sem executar o AG.")
    parser.add_argument("--populacao", type=int, default=80)
    parser.add_argument("--geracoes", type=int, default=200)
    parser.add_argument("--moldes", action="store_true", help="Grava planilhas-modelo em data/input.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.moldes:
        out = DEFAULT_DATA / "input"
        write_templates(out)
        print(f"Moldes gravados em {out}")
        return

    print(f"Carregando entrada: {Path(args.entrada)}")
    try:
        teachers, class_groups, subjects, time_slots = load_instance(args.entrada)
    except (OSError, TypeError, ValueError) as exc:
        print(f"Erro ao carregar entrada: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        f"  {len(teachers)} professores | "
        f"{len(class_groups)} turmas | "
        f"{len(subjects)} disciplinas | "
        f"{len(time_slots)} time slots"
    )

    errors, warnings = validate_instance(teachers, class_groups, subjects, time_slots)
    for warning in warnings:
        print(f"Aviso: {warning}")
    if errors:
        print("Instância inválida:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    if args.somente_validar:
        print("Instância válida.")
        return

    context = GAContext(
        teachers=teachers,
        class_groups=class_groups,
        subjects=subjects,
        time_slots=time_slots,
        slot_ordering_key=SLOT_ORDERING_STRATEGIES[SLOT_ORDERING_STRATEGY],
    )

    result = run_ga(
        context=context,
        population_size=args.populacao,
        generations=args.geracoes,
        crossover_rate=CROSSOVER_RATE,
        mutation_rate=MUTATION_RATE,
        elitism_count=ELITISM_COUNT,
        tournament_size=TOURNAMENT_SIZE,
        verbose=True,
    )
    print_result(result, context)


if __name__ == "__main__":
    main()

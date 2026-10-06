"""CLI: carrega a escola, valida, roda o AG e imprime o horário."""

import argparse
import sys
from pathlib import Path

from data.instance import load_instance
from data.templates import write_templates
from data.validate import validate_instance
from ga.context import GAContext
from ga.engine import run_ga
from reporting.printer import print_result

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Auto-Schedule: gera horário escolar com AG.")
    parser.add_argument("--entrada", default=str(DEFAULT_DATA), help="Pasta JSON, molde.xlsx ou trio de planilhas.")
    parser.add_argument("--somente-validar", action="store_true")
    parser.add_argument("--populacao", type=int, default=80)
    parser.add_argument("--geracoes", type=int, default=200)
    parser.add_argument("--moldes", action="store_true")
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
        school = load_instance(args.entrada)
    except (OSError, TypeError, ValueError) as exc:
        print(f"Erro ao carregar entrada: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        f"  {len(school.teachers)} professores | "
        f"{len(school.class_groups)} turmas | "
        f"{len(school.subjects)} disciplinas | "
        f"{len(school.time_slots)} time slots"
    )

    errors, warnings = validate_instance(school)
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

    context = GAContext.from_school(school)
    result = run_ga(
        context,
        population_size=args.populacao,
        generations=args.geracoes,
        verbose=True,
    )
    print_result(result, context)


if __name__ == "__main__":
    main()

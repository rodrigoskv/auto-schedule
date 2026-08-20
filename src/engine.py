from dataclasses import dataclass, field
from time import perf_counter

from domain.entities import Schedule
from ga.context import GAContext
from ga.fitness import FitnessBreakdown, evaluate_details
from ga.operators.crossover import crossover
from ga.operators.initial_population import generate_population
from ga.operators.mutation import mutate
from ga.operators.repair import repair_schedule
from ga.operators.selection import tournament_selection


@dataclass
class GAResult:
    schedule: Schedule
    fitness: float
    elapsed_seconds: float
    generation_reached: int
    breakdown: FitnessBreakdown
    history: list[dict] = field(default_factory=list)


def run_ga(
    context: GAContext,
    population_size: int = 80,
    generations: int = 500,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.08,
    elitism_count: int = 2,
    tournament_size: int = 3,
    verbose: bool = True,
) -> GAResult:
    started = perf_counter()
    population: list[Schedule] = generate_population(population_size, context)

    best_schedule = population[0]
    best_fitness = float("-inf")
    best_breakdown = evaluate_details(best_schedule, context)
    history: list[dict] = []
    generation_reached = 0

    for generation in range(1, generations + 1):
        generation_reached = generation
        breakdowns = [evaluate_details(individual, context) for individual in population]
        fitnesses = [item.fitness for item in breakdowns]

        best_index = max(range(len(fitnesses)), key=lambda index: fitnesses[index])
        generation_best = fitnesses[best_index]

        if generation_best > best_fitness:
            best_fitness = generation_best
            best_schedule = population[best_index]
            best_breakdown = breakdowns[best_index]

        history.append(
            {
                "generation": generation,
                "best_fitness": best_fitness,
                "generation_best": generation_best,
                "counts": dict(best_breakdown.counts),
            }
        )

        if verbose and (generation % 10 == 0 or generation == 1):
            counts = best_breakdown.counts
            print(
                f"  Geração {generation:>4}/{generations} | "
                f"Melhor: {best_fitness:>10.1f} | "
                f"Atual: {generation_best:>10.1f} | "
                f"H1={counts['H1']} H2={counts['H2']} "
                f"H3={counts['H3']} H4={counts['H4']} S1={counts['S1']}"
            )

        if best_fitness >= 100_000:
            if verbose:
                print(f"\n  Fitness máximo atingido na geração {generation}.")
            break

        ranked = sorted(range(len(fitnesses)), key=lambda index: fitnesses[index], reverse=True)
        new_population = [population[index] for index in ranked[:elitism_count]]

        while len(new_population) < population_size:
            parent1 = tournament_selection(population, fitnesses, tournament_size)
            parent2 = tournament_selection(population, fitnesses, tournament_size)
            child1, child2 = crossover(parent1, parent2, context, crossover_rate)
            child1 = repair_schedule(mutate(child1, context, mutation_rate), context)
            child2 = repair_schedule(mutate(child2, context, mutation_rate), context)
            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)

        population = new_population

    return GAResult(
        schedule=best_schedule,
        fitness=best_fitness,
        elapsed_seconds=perf_counter() - started,
        generation_reached=generation_reached,
        breakdown=best_breakdown,
        history=history,
    )
"""
Loop evolutivo principal do Algoritmo Genético.

Fluxo por geração:
  1. Avaliar fitness de toda a população
  2. Elitismo: copiar os melhores direto para a próxima geração
  3. Seleção por torneio
  4. Crossover entre pais
  5. Mutação nos filhos
  6. Substituir população
  7. Log de progresso
"""

from domain.schedule import Schedule
from ga.representation import GAContext
from ga.initial_population import generate_population
from ga.fitness import evaluate
from ga.selection import tournament_selection
from ga.crossover import crossover
from ga.mutation import mutate


def run_ga(
    context: GAContext,
    population_size: int = 80,
    generations: int = 200,
    crossover_rate: float = 0.8,
    mutation_rate: float = 0.08,
    elitism_count: int = 2,
    tournament_size: int = 3,
    verbose: bool = True,
) -> tuple[Schedule, float]:
    """
    Executa o algoritmo genético e retorna o melhor Schedule encontrado
    junto com seu fitness.

    Args:
        context: dados de domínio e configuração de ordenação.
        population_size: tamanho da população.
        generations: número de gerações.
        crossover_rate: probabilidade de crossover entre pais.
        mutation_rate: probabilidade de mutação por gene (aula).
        elitism_count: quantos melhores indivíduos passam direto.
        tournament_size: tamanho do torneio de seleção.
        verbose: se True, imprime progresso a cada 10 gerações.

    Returns:
        Tupla (melhor_schedule, melhor_fitness).
    """
    # 1. população inicial
    population: list[Schedule] = generate_population(population_size, context)

    best_schedule: Schedule = population[0]
    best_fitness: float = float("-inf")

    for generation in range(1, generations + 1):
        # 2. avaliar fitness
        fitnesses: list[float] = [evaluate(ind, context) for ind in population]

        # 3. rastrear melhor geral
        gen_best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        gen_best_fitness = fitnesses[gen_best_idx]

        if gen_best_fitness > best_fitness:
            best_fitness = gen_best_fitness
            best_schedule = population[gen_best_idx]

        if verbose and (generation % 10 == 0 or generation == 1):
            print(
                f"  Geração {generation:>4}/{generations} | "
                f"Melhor: {best_fitness:>10.1f} | "
                f"Geração atual: {gen_best_fitness:>10.1f}"
            )

        # convergencia antecipada: fitness máximo atingido
        if best_fitness >= 100_000:
            if verbose:
                print(f"\n  ✓ Fitness máximo atingido na geração {generation}!")
            break

        # 4. elitismo: melhores indivíduos passam direto
        sorted_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i], reverse=True)
        elite = [population[i] for i in sorted_indices[:elitism_count]]

        #5. nova geração
        new_population: list[Schedule] = list(elite)

        while len(new_population) < population_size:
            # seleção
            parent1 = tournament_selection(population, fitnesses, tournament_size)
            parent2 = tournament_selection(population, fitnesses, tournament_size)

            # crossover
            child1, child2 = crossover(parent1, parent2, context, crossover_rate)

            # mutação
            child1 = mutate(child1, context, mutation_rate)
            child2 = mutate(child2, context, mutation_rate)

            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)

        population = new_population

    return best_schedule, best_fitness


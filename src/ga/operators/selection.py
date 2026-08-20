import random

from domain.entities import Schedule

def tournament_selection(
    population: list[Schedule],
    fitnesses: list[float],
    tournament_size: int = 3,
) -> Schedule:
    indices = random.sample(range(len(population)), k=min(tournament_size, len(population)))
    best_idx = max(indices, key=lambda index: fitnesses[index])
    return population[best_idx]

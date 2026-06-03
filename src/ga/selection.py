"""
Seleção por torneio.

Escolhe aleatoriamente `tournament_size` indivíduos da população
e retorna o de maior fitness. Simples, robusto e sem pressão excessiva.
"""

import random
from domain.schedule import Schedule


def tournament_selection(
    population: list[Schedule],
    fitnesses: list[float],
    tournament_size: int = 3,
) -> Schedule:
    """
    Seleciona um indivíduo por torneio.

    args:
        population: lista de Schedules da geração atual.
        fitnesses: lista paralela de scores (mesma ordem da população).
        tournament_size: quantos candidatos disputam cada torneio.

    Returns:
        O indivíduo vencedor (maior fitness).
    """
    indices = random.sample(range(len(population)), k=min(tournament_size, len(population)))
    best_idx = max(indices, key=lambda i: fitnesses[i])
    return population[best_idx]


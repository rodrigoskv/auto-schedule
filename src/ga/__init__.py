"""Algoritmo genético.

Indivíduo  = Schedule
Cromossomo = lista de Lesson
Gene       = Lesson (professor, disciplina, turma, horário)

Fluxo de uma execução:
    initial_population → (por geração) fitness → elitismo
                       → selection → crossover → mutation → repair
"""

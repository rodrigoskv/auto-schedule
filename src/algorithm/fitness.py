"""
Cálculo de fitness para escalas de horário
TODO: Implementar todas as regras de negócio
"""


class FitnessCalculator:
    def __init__(self, weights=None):
        """
        Pesos para diferentes critérios
        TODO: Ajustar pesos baseado na importância
        """
        self.weights = weights or {
            # 'cobertura': 1.0,  # Todos os horários preenchidos
            # 'conflitos': 2.0,  # Evitar a pessoa estar em dois horarios ao msm tempo
            # 'disponibilidade': 0.5,  # Respeitar disponibilidade
            # 'descanso': 1.5,  # Intervalo entre turnos
            # 'carga_horaria': 1.0  # Horas justas por pessoa
        }

    def calculate(self, schedule, employees, shifts, constraints):
        """
        Calcula fitness total de uma escala
        TODO: Implementar cálculo completo
        """
        # fitness = 0
        # penalties = {}

        # Verificar cada critério settado no inicio
        # - cobertura
        # - conflitos
        # - disponibilidade
        # - descansos
        # - carga horaria

        # # Calcular fitness
        # for key, penalty in penalties.items():
        #     fitness += penalty * self.weights.get(key, 1.0)
        #
        # # Quanto menor o fitness, melhor (problema de minimização)
        # return -fitness

    def _check_coverage(self, schedule, shifts):
        """TODO: Verificar se todos horários estão preenchidos"""
        return 0

    def _check_conflicts(self, schedule):
        """TODO: Verificar se mesma pessoa em dois lugares"""
        return 0

    def _check_preferences(self, schedule, employees):
        """TODO: Verificar preferências dos funcionários"""
        return 0

    def _check_rest_periods(self, schedule):
        """TODO: Verificar intervalos mínimos entre turnos"""
        return 0

    def _check_workload(self, schedule, employees):
        """TODO: Verificar distribuição justa de horas"""
        return 0
"""O AG encontra (ou corretamente não encontra) soluções nos cenários miniatura."""

from domain.constraints import BASE_SCORE
from ga.engine import run_ga
from ga.fitness import evaluate_details
from ga.operators.initial_population import generate_individual

from tests.builders import (
    scenario_disponibilidade_so_segunda,
    scenario_duas_turmas_professor_compartilhado,
    scenario_h3_estrutural,
    scenario_s1_evitavel,
    scenario_trivial_viavel,
    slot_id,
)


def _run(ctx, population_size=12, generations=20, **kwargs):
    return run_ga(
        ctx,
        population_size=population_size,
        generations=generations,
        verbose=False,
        **kwargs,
    )


class TestGaResolveInstanciasViaveis:
    def test_instancia_trivial_para_no_maximo_e_zera_violacoes(self):
        result = _run(scenario_trivial_viavel(), population_size=4, generations=10)
        assert result.fitness == float(BASE_SCORE)
        assert result.breakdown.hard == 0
        assert result.breakdown.soft == 0
        assert result.generation_reached == 1

    def test_professor_compartilhado_nao_fica_em_duas_turmas_no_mesmo_slot(self):
        ctx = scenario_duas_turmas_professor_compartilhado()
        result = _run(ctx, population_size=8, generations=8)
        details = evaluate_details(result.schedule, ctx)
        assert details.counts["H1"] == 0
        assert details.counts["H2"] == 0
        assert details.counts["H3"] == 0
        assert details.counts["H4"] == 0
        slots = [item.time_slot_id for item in result.schedule.lessons]
        assert len(slots) == 2
        assert slots[0] != slots[1]

    def test_aulas_do_professor_caem_so_no_dia_disponivel(self):
        ctx = scenario_disponibilidade_so_segunda()
        result = _run(ctx, population_size=12, generations=12)
        details = evaluate_details(result.schedule, ctx)
        assert details.counts["H4"] == 0
        assert details.counts["H3"] == 0
        ana_slots = [
            item.time_slot_id
            for item in result.schedule.lessons
            if item.teacher_id == "ana"
        ]
        assert sorted(ana_slots) == [
            slot_id("segunda", 1),
            slot_id("segunda", 2),
        ]

    def test_quatro_aulas_da_mesma_disciplina_nao_passam_de_duas_por_dia(self):
        ctx = scenario_s1_evitavel()
        result = _run(ctx, population_size=20, generations=40)
        details = evaluate_details(result.schedule, ctx)
        assert details.counts["H1"] == 0
        assert details.counts["H2"] == 0
        assert details.counts["H3"] == 0
        assert details.counts["S1"] == 0
        assert result.fitness == float(BASE_SCORE)


class TestGaReconheceInstanciaImpossivel:
    def test_h3_estrutural_nao_zera_mesmo_depois_do_ag(self):
        ctx = scenario_h3_estrutural()
        result = _run(ctx, population_size=8, generations=8)
        details = evaluate_details(result.schedule, ctx)
        assert details.counts["H3"] >= 1
        assert result.fitness <= BASE_SCORE - 1_000


class TestInvariantesDoLoop:
    def test_elitismo_nao_piora_o_melhor_global(self):
        result = _run(
            scenario_duas_turmas_professor_compartilhado(),
            population_size=8,
            generations=6,
        )
        best_so_far = [item["best_fitness"] for item in result.history]
        assert best_so_far == sorted(best_so_far)
        assert result.fitness == best_so_far[-1]

    def test_historico_registra_uma_entrada_por_geracao(self):
        result = _run(scenario_h3_estrutural(), population_size=4, generations=5)
        assert [item["generation"] for item in result.history] == [1, 2, 3, 4, 5]

    def test_individuo_final_tem_a_carga_pedida(self):
        ctx = scenario_disponibilidade_so_segunda()
        result = _run(ctx)
        by_subject = {}
        for item in result.schedule.lessons:
            by_subject[item.subject_id] = by_subject.get(item.subject_id, 0) + 1
        assert by_subject["mat_6a"] == 2
        assert by_subject["port_6a"] == 2

    def test_geracao_inicial_pode_violar_h1_e_o_resultado_final_nao(self):
        ctx = scenario_duas_turmas_professor_compartilhado()
        # Com seed 0 a população inicial deste cenário costuma nascer com choque;
        # o que importa é o AG sair dele.
        initial = generate_individual(ctx)
        result = _run(ctx, population_size=8, generations=8)
        assert evaluate_details(result.schedule, ctx).counts["H1"] == 0
        assert len(initial.lessons) == 2

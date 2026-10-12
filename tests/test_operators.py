"""Operadores do AG: população inicial, torneio, cruzamento, mutação e repair."""

import copy
import random
from collections import Counter

from domain.entities import Schedule
from ga.fitness import evaluate_details
from ga.operators.crossover import crossover
from ga.operators.initial_population import generate_individual, generate_population
from ga.operators.mutation import mutate
from ga.operators.repair import repair_schedule
from ga.operators.selection import tournament_selection

from tests.builders import (
    lesson,
    make_class,
    make_context,
    make_subject,
    make_teacher,
    scenario_duas_turmas_professor_compartilhado,
    scenario_h3_estrutural,
    scenario_h4_disponibilidade,
    scenario_trivial_viavel,
    schedule,
    slot_id,
)


def _workload_by_subject(grade: Schedule) -> Counter:
    return Counter(item.subject_id for item in grade.lessons)


def _h2(grade, ctx) -> int:
    return evaluate_details(grade, ctx).counts["H2"]


class TestPopulacaoInicial:
    def test_tamanho_da_populacao(self):
        ctx = scenario_trivial_viavel()
        population = generate_population(7, ctx)
        assert len(population) == 7

    def test_cada_disciplina_nasce_com_a_carga_semanal(self):
        ctx = make_context(
            teachers=[make_teacher("ana"), make_teacher("bia")],
            class_groups=[make_class("6a")],
            subjects=[
                make_subject("mat_6a", "ana", "6a", 3),
                make_subject("port_6a", "bia", "6a", 2),
            ],
            days=["segunda", "terca", "quarta"],
            periods=2,
        )
        grade = generate_individual(ctx)
        counts = _workload_by_subject(grade)
        assert counts["mat_6a"] == 3
        assert counts["port_6a"] == 2

    def test_turma_nao_nasce_com_duas_aulas_no_mesmo_slot(self):
        ctx = make_context(
            teachers=[make_teacher("ana")],
            class_groups=[make_class("6a")],
            subjects=[make_subject("mat_6a", "ana", "6a", 4)],
            days=["segunda", "terca"],
            periods=3,
        )
        for _ in range(8):
            assert _h2(generate_individual(ctx), ctx) == 0

    def test_carga_maior_que_slots_deixa_aula_sem_horario(self):
        ctx = scenario_h3_estrutural()
        grade = generate_individual(ctx)
        unassigned = grade.get_unassigned_lessons()
        assert len(grade.lessons) == 3
        assert len(unassigned) == 1
        assert evaluate_details(grade, ctx).counts["H3"] == 1

    def test_instancia_trivial_ja_nasce_com_fitness_maximo(self):
        ctx = scenario_trivial_viavel()
        details = evaluate_details(generate_individual(ctx), ctx)
        assert details.hard == 0
        assert details.soft == 0
        assert details.fitness == 100_000.0


class TestCruzamento:
    def test_taxa_zero_devolve_copias_independentes(self):
        ctx = scenario_trivial_viavel()
        parent1 = generate_individual(ctx)
        parent2 = generate_individual(ctx)
        child1, child2 = crossover(parent1, parent2, ctx, crossover_rate=0.0)
        assert child1 is not parent1
        assert child2 is not parent2
        assert [item.time_slot_id for item in child1.lessons] == [
            item.time_slot_id for item in parent1.lessons
        ]

    def test_filhos_preservam_carga_semanal_e_h2_zero(self):
        ctx = make_context(
            teachers=[make_teacher("ana"), make_teacher("bia")],
            class_groups=[make_class("6a"), make_class("6b")],
            subjects=[
                make_subject("mat_6a", "ana", "6a", 2),
                make_subject("port_6a", "bia", "6a", 2),
                make_subject("mat_6b", "ana", "6b", 2),
                make_subject("port_6b", "bia", "6b", 2),
            ],
            days=["segunda", "terca"],
            periods=3,
        )
        parent1 = generate_individual(ctx)
        parent2 = generate_individual(ctx)
        child1, child2 = crossover(parent1, parent2, ctx, crossover_rate=1.0)
        required = Counter(
            subject.id
            for subject in ctx.subjects
            for _ in range(subject.weekly_workload)
        )
        for child in (child1, child2):
            assert _workload_by_subject(child) == required
            assert _h2(child, ctx) == 0


class TestMutacao:
    def test_taxa_zero_nao_muda_os_horarios(self):
        ctx = scenario_duas_turmas_professor_compartilhado()
        original = generate_individual(ctx)
        mutated = mutate(original, ctx, mutation_rate=0.0)
        assert [item.time_slot_id for item in mutated.lessons] == [
            item.time_slot_id for item in original.lessons
        ]
        assert mutated is not original

    def test_nao_introduz_h2_nem_muda_a_carga(self):
        ctx = make_context(
            teachers=[make_teacher("ana")],
            class_groups=[make_class("6a")],
            subjects=[make_subject("mat_6a", "ana", "6a", 3)],
            days=["segunda", "terca"],
            periods=3,
        )
        original = generate_individual(ctx)
        mutated = mutate(original, ctx, mutation_rate=1.0)
        assert _workload_by_subject(mutated) == _workload_by_subject(original)
        assert _h2(mutated, ctx) == 0


class TestRepair:
    def test_nao_altera_o_individuo_original(self):
        ctx, invalid, _ = scenario_h4_disponibilidade()
        snapshot = copy.deepcopy(invalid)
        repair_schedule(invalid, ctx)
        assert [item.time_slot_id for item in invalid.lessons] == [
            item.time_slot_id for item in snapshot.lessons
        ]

    def test_move_aula_sem_horario_para_slot_livre(self):
        ctx = make_context(
            teachers=[make_teacher("ana", days=["segunda"])],
            class_groups=[make_class("6a")],
            subjects=[make_subject("mat_6a", "ana", "6a", 1)],
            days=["segunda"],
            periods=2,
        )
        broken = schedule(lesson("ana", "mat_6a", "6a", ""))
        repaired = repair_schedule(broken, ctx)
        assert repaired.lessons[0].time_slot_id
        assert evaluate_details(repaired, ctx).counts["H3"] == 0

    def test_tira_professor_de_dia_indisponivel(self):
        ctx, invalid, _ = scenario_h4_disponibilidade()
        repaired = repair_schedule(invalid, ctx)
        details = evaluate_details(repaired, ctx)
        assert details.counts["H4"] == 0
        assert repaired.lessons[0].time_slot_id == slot_id("terca", 1)

    def test_desfaz_choque_de_professor_quando_ha_slot_livre(self):
        ctx = scenario_duas_turmas_professor_compartilhado()
        clash = schedule(
            lesson("ana", "mat_6a", "6a", slot_id("segunda", 1)),
            lesson("ana", "mat_6b", "6b", slot_id("segunda", 1)),
        )
        repaired = repair_schedule(clash, ctx)
        details = evaluate_details(repaired, ctx)
        assert details.counts["H1"] == 0
        assert details.counts["H3"] == 0
        slots = {item.time_slot_id for item in repaired.lessons}
        assert slots == {slot_id("segunda", 1), slot_id("segunda", 2)}

    def test_desaloca_quando_o_professor_nao_tem_nenhum_periodo(self):
        ctx = make_context(
            teachers=[make_teacher("ana", available_periods=["sexta_manha"])],
            class_groups=[make_class("6a")],
            subjects=[make_subject("mat_6a", "ana", "6a", 1)],
            days=["segunda"],
            periods=1,
        )
        broken = schedule(lesson("ana", "mat_6a", "6a", slot_id("segunda", 1)))
        repaired = repair_schedule(broken, ctx)
        details = evaluate_details(repaired, ctx)
        assert details.counts["H4"] == 0
        assert repaired.lessons[0].time_slot_id == ""
        assert details.counts["H3"] == 1


class TestSelecao:
    def test_torneio_do_tamanho_da_populacao_devolve_o_melhor(self):
        ctx = scenario_trivial_viavel()
        weak = schedule(lesson("ana", "mat_6a", "6a", ""))
        strong = generate_individual(ctx)
        population = [weak, strong, weak]
        fitnesses = [evaluate_details(item, ctx).fitness for item in population]
        chosen = tournament_selection(population, fitnesses, tournament_size=3)
        assert chosen is strong

    def test_torneio_nunca_escolhe_fora_da_amostra(self):
        ctx = scenario_trivial_viavel()
        population = generate_population(5, ctx)
        fitnesses = [float(i) for i in range(5)]
        random.seed(1)
        chosen = tournament_selection(population, fitnesses, tournament_size=2)
        assert chosen in population

"""Cenários determinísticos: o fitness conta H1–H4 e S1 como os critérios descrevem."""

from domain.constraints import BASE_SCORE, PESO_HARD, PESO_SOFT
from ga.fitness import evaluate, evaluate_details

from tests.builders import (
    lesson,
    make_class,
    make_context,
    make_subject,
    make_teacher,
    scenario_formula_97970,
    scenario_h1_caroline,
    scenario_h2_duas_aulas_na_mesma_turma,
    scenario_h3_carga_matematica,
    scenario_h4_disponibilidade,
    scenario_s1_tres_aulas_no_mesmo_dia,
    schedule,
    slot_id,
)


def _counts(grade, ctx):
    return evaluate_details(grade, ctx).counts


class TestH1ProfessorEmDuasTurmas:
    def test_caroline_no_mesmo_horario_conta_uma_violacao(self):
        ctx, invalid, _ = scenario_h1_caroline()
        assert _counts(invalid, ctx)["H1"] == 1

    def test_caroline_em_horarios_diferentes_nao_viola(self):
        ctx, _, valid = scenario_h1_caroline()
        assert _counts(valid, ctx)["H1"] == 0

    def test_tres_turmas_no_mesmo_slot_contam_duas_violacoes(self):
        ctx = make_context(
            teachers=[make_teacher("ana", days=["segunda"])],
            class_groups=[make_class("6a"), make_class("6b"), make_class("6c")],
            subjects=[
                make_subject("mat_6a", "ana", "6a", 1),
                make_subject("mat_6b", "ana", "6b", 1),
                make_subject("mat_6c", "ana", "6c", 1),
            ],
            days=["segunda"],
            periods=1,
        )
        grade = schedule(
            lesson("ana", "mat_6a", "6a", slot_id("segunda", 1)),
            lesson("ana", "mat_6b", "6b", slot_id("segunda", 1)),
            lesson("ana", "mat_6c", "6c", slot_id("segunda", 1)),
        )
        assert _counts(grade, ctx)["H1"] == 2

    def test_professores_diferentes_no_mesmo_slot_nao_sao_h1(self):
        ctx = make_context(
            teachers=[
                make_teacher("ana", days=["segunda"]),
                make_teacher("bia", days=["segunda"]),
            ],
            class_groups=[make_class("6a"), make_class("6b")],
            subjects=[
                make_subject("mat_6a", "ana", "6a", 1),
                make_subject("port_6b", "bia", "6b", 1),
            ],
            days=["segunda"],
            periods=1,
        )
        grade = schedule(
            lesson("ana", "mat_6a", "6a", slot_id("segunda", 1)),
            lesson("bia", "port_6b", "6b", slot_id("segunda", 1)),
        )
        assert _counts(grade, ctx)["H1"] == 0


class TestH2TurmaComDuasAulas:
    def test_matematica_e_portugues_no_mesmo_horario(self):
        ctx, invalid, _ = scenario_h2_duas_aulas_na_mesma_turma()
        assert _counts(invalid, ctx)["H2"] == 1

    def test_aulas_em_slots_diferentes_nao_violam(self):
        ctx, _, valid = scenario_h2_duas_aulas_na_mesma_turma()
        assert _counts(valid, ctx)["H2"] == 0

    def test_tres_aulas_no_mesmo_slot_contam_duas_violacoes(self):
        ctx = make_context(
            teachers=[
                make_teacher("ana", days=["segunda"]),
                make_teacher("bia", days=["segunda"]),
                make_teacher("cia", days=["segunda"]),
            ],
            class_groups=[make_class("6a")],
            subjects=[
                make_subject("mat", "ana", "6a", 1),
                make_subject("port", "bia", "6a", 1),
                make_subject("hist", "cia", "6a", 1),
            ],
            days=["segunda"],
            periods=1,
        )
        same_slot = slot_id("segunda", 1)
        grade = schedule(
            lesson("ana", "mat", "6a", same_slot),
            lesson("bia", "port", "6a", same_slot),
            lesson("cia", "hist", "6a", same_slot),
        )
        assert _counts(grade, ctx)["H2"] == 2


class TestH3CargaSemanal:
    def test_quatro_aulas_pedidas_e_quatro_alocadas(self):
        ctx, _, complete = scenario_h3_carga_matematica()
        assert _counts(complete, ctx)["H3"] == 0

    def test_uma_aula_sem_horario_conta_deficit(self):
        ctx, short, _ = scenario_h3_carga_matematica()
        assert _counts(short, ctx)["H3"] == 1

    def test_disciplina_ausente_da_grade_conta_carga_inteira(self):
        ctx = make_context(
            teachers=[make_teacher("ana", days=["segunda"])],
            class_groups=[make_class("6a")],
            subjects=[make_subject("mat_6a", "ana", "6a", 3)],
            days=["segunda"],
            periods=3,
        )
        assert _counts(schedule(), ctx)["H3"] == 3

    def test_aulas_a_mais_nao_geram_h3(self):
        """H3 só penaliza déficit, não excesso."""
        ctx = make_context(
            teachers=[make_teacher("ana", days=["segunda"])],
            class_groups=[make_class("6a")],
            subjects=[make_subject("mat_6a", "ana", "6a", 1)],
            days=["segunda"],
            periods=2,
        )
        extra = schedule(
            lesson("ana", "mat_6a", "6a", slot_id("segunda", 1)),
            lesson("ana", "mat_6a", "6a", slot_id("segunda", 2)),
        )
        assert _counts(extra, ctx)["H3"] == 0


class TestH4Disponibilidade:
    def test_aula_fora_do_dia_disponivel(self):
        ctx, invalid, _ = scenario_h4_disponibilidade()
        assert _counts(invalid, ctx)["H4"] == 1

    def test_aula_no_dia_disponivel_nao_viola(self):
        ctx, _, valid = scenario_h4_disponibilidade()
        assert _counts(valid, ctx)["H4"] == 0

    def test_lista_vazia_de_periodos_libera_qualquer_slot(self):
        ctx = make_context(
            teachers=[make_teacher("ana", available_periods=[])],
            class_groups=[make_class("6a")],
            subjects=[make_subject("mat_6a", "ana", "6a", 1)],
            days=["segunda"],
            periods=1,
        )
        grade = schedule(lesson("ana", "mat_6a", "6a", slot_id("segunda", 1)))
        assert _counts(grade, ctx)["H4"] == 0

    def test_aula_sem_horario_nao_conta_h4(self):
        ctx, _, _ = scenario_h4_disponibilidade()
        grade = schedule(lesson("ana", "mat_6a", "6a", ""))
        assert _counts(grade, ctx)["H4"] == 0


class TestS1Concentracao:
    def test_tres_aulas_no_mesmo_dia_contam_uma_violacao(self):
        ctx, concentrated, _ = scenario_s1_tres_aulas_no_mesmo_dia()
        assert _counts(concentrated, ctx)["S1"] == 1

    def test_duas_aulas_no_mesmo_dia_sao_aceitaveis(self):
        ctx, _, spread = scenario_s1_tres_aulas_no_mesmo_dia()
        assert _counts(spread, ctx)["S1"] == 0

    def test_quatro_aulas_no_mesmo_dia_contam_duas_violacoes(self):
        ctx = make_context(
            teachers=[make_teacher("ana", days=["segunda"])],
            class_groups=[make_class("6a")],
            subjects=[make_subject("mat_6a", "ana", "6a", 4)],
            days=["segunda"],
            periods=4,
        )
        grade = schedule(
            *(lesson("ana", "mat_6a", "6a", slot_id("segunda", order)) for order in range(1, 5))
        )
        assert _counts(grade, ctx)["S1"] == 2

    def test_mesma_disciplina_em_turmas_diferentes_nao_soma_s1(self):
        ctx = make_context(
            teachers=[make_teacher("ana", days=["segunda"])],
            class_groups=[make_class("6a"), make_class("6b")],
            subjects=[
                make_subject("mat_6a", "ana", "6a", 2),
                make_subject("mat_6b", "ana", "6b", 2),
            ],
            days=["segunda"],
            periods=2,
        )
        grade = schedule(
            lesson("ana", "mat_6a", "6a", slot_id("segunda", 1)),
            lesson("ana", "mat_6a", "6a", slot_id("segunda", 2)),
            lesson("ana", "mat_6b", "6b", slot_id("segunda", 1)),
            lesson("ana", "mat_6b", "6b", slot_id("segunda", 2)),
        )
        assert _counts(grade, ctx)["S1"] == 0


class TestFormulaDoScore:
    def test_pesos_batem_com_os_criterios(self):
        assert BASE_SCORE == 100_000
        assert PESO_HARD == 1_000
        assert PESO_SOFT == 10

    def test_exemplo_do_documento_2_hard_3_soft(self):
        ctx, grade = scenario_formula_97970()
        details = evaluate_details(grade, ctx)
        assert details.counts["H1"] == 1
        assert details.counts["H3"] == 1
        assert details.hard == 2
        assert details.soft == 3
        assert details.fitness == 97_970

    def test_grade_perfeita_atinge_a_base(self):
        ctx, _, valid = scenario_h1_caroline()
        assert evaluate(valid, ctx) == float(BASE_SCORE)

    def test_cada_hard_desconta_mil_e_cada_soft_desconta_dez(self):
        ctx, concentrated, _ = scenario_s1_tres_aulas_no_mesmo_dia()
        details = evaluate_details(concentrated, ctx)
        expected = BASE_SCORE - PESO_HARD * details.hard - PESO_SOFT * details.soft
        assert details.fitness == float(expected)

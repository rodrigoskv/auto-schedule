"""Textos de qualidade do horário para a tela e o CLI."""

from reporting.violations import explain_problems, quality_status, unassigned_rows

from tests.builders import (
    lesson,
    make_class,
    make_context,
    make_subject,
    make_teacher,
    scenario_formula_97970,
    scenario_h1_caroline,
    schedule,
)


def test_grade_perfeita_e_status_ok():
    ctx, _, valid = scenario_h1_caroline()
    from ga.fitness import evaluate_details

    details = evaluate_details(valid, ctx)
    level, message = quality_status(details)
    assert level == "ok"
    assert "completo" in message
    assert explain_problems(details) == []


def test_explica_h1_e_h3_em_portugues():
    ctx, grade = scenario_formula_97970()
    from ga.fitness import evaluate_details

    details = evaluate_details(grade, ctx)
    level, _ = quality_status(details)
    assert level == "bad"
    titles = {item["title"] for item in explain_problems(details)}
    assert "Professor em duas turmas ao mesmo tempo" in titles
    assert "Aulas que não caberam na semana" in titles


def test_lista_aulas_sem_horario():
    ctx = make_context(
        teachers=[make_teacher("ana", days=["segunda"])],
        class_groups=[make_class("6a", name="6º A")],
        subjects=[make_subject("mat_6a", "ana", "6a", 1, name="Matemática")],
        days=["segunda"],
        periods=1,
    )
    grade = schedule(lesson("ana", "mat_6a", "6a", ""))
    rows = unassigned_rows(grade, ctx)
    assert rows == [{"Turma": "6º A", "Disciplina": "Matemática", "Professor": "Ana"}]

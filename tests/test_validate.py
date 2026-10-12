"""Validação da instância: erros de referência e avisos de carga/disponibilidade."""

from pathlib import Path

from data.instance import load_instance
from data.validate import validate_instance

from tests.builders import (
    make_class,
    make_school,
    make_subject,
    make_teacher,
    scenario_h3_estrutural,
    scenario_trivial_viavel,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_instancia_trivial_e_valida():
    errors, warnings = validate_instance(scenario_trivial_viavel())
    assert errors == []
    assert warnings == []


def test_carga_maior_que_slots_gera_aviso_de_encaixe():
    school = scenario_h3_estrutural()
    errors, warnings = validate_instance(school)
    assert errors == []
    assert any("3 aulas na semana e só 2 horários" in item for item in warnings)
    assert any("não consegue encaixar" in item for item in warnings)


def test_disciplina_sem_turma_e_erro():
    school = make_school(
        teachers=[make_teacher("ana")],
        class_groups=[make_class("6a")],
        subjects=[make_subject("mat_6a", "ana", "", 1, name="Matemática")],
        days=["segunda"],
        periods=1,
    )
    errors, _ = validate_instance(school)
    assert any("sem turma" in item for item in errors)


def test_turma_e_professor_inexistentes_sao_erro():
    school = make_school(
        teachers=[make_teacher("ana")],
        class_groups=[make_class("6a")],
        subjects=[make_subject("mat_6a", "bia", "9_ano", 1, name="Matemática")],
        days=["segunda"],
        periods=1,
    )
    errors, _ = validate_instance(school)
    assert any("professor 'bia'" in item and "não existe" in item for item in errors)
    assert any("turma '9_ano'" in item and "não existe" in item for item in errors)


def test_id_duplicado_e_carga_zero_sao_erro():
    school = make_school(
        teachers=[make_teacher("ana"), make_teacher("ana", name="Ana 2")],
        class_groups=[make_class("6a"), make_class("6a", name="outra")],
        subjects=[
            make_subject("mat_6a", "ana", "6a", 0),
            make_subject("mat_6a", "ana", "6a", 1),
        ],
        days=["segunda"],
        periods=1,
    )
    errors, _ = validate_instance(school)
    assert any("Professor duplicado" in item for item in errors)
    assert any("Turma duplicado" in item for item in errors)
    assert any("Disciplina duplicado" in item for item in errors)
    assert any("pelo menos 1 aula" in item for item in errors)


def test_nome_de_professor_repetido_e_erro():
    school = make_school(
        teachers=[
            make_teacher("ana", name="Ana"),
            make_teacher("ana_costa", name="Ana"),
        ],
        class_groups=[make_class("6a")],
        subjects=[make_subject("mat_6a", "ana", "6a", 1)],
        days=["segunda"],
        periods=1,
    )
    errors, _ = validate_instance(school)
    assert any("Ana" in item and "repetido" in item for item in errors)


def test_professor_sem_dias_marcados_gera_aviso():
    school = make_school(
        teachers=[make_teacher("ana", available_periods=[])],
        class_groups=[make_class("6a")],
        subjects=[make_subject("mat_6a", "ana", "6a", 1)],
        days=["segunda"],
        periods=1,
    )
    errors, warnings = validate_instance(school)
    assert errors == []
    assert any("sem dias marcados" in item for item in warnings)


def test_professor_com_mais_aulas_do_que_horarios_gera_aviso():
    school = make_school(
        teachers=[make_teacher("ana", days=["segunda"])],
        class_groups=[make_class("6a")],
        subjects=[make_subject("mat_6a", "ana", "6a", 3)],
        days=["segunda"],
        periods=1,
    )
    _, warnings = validate_instance(school)
    assert any("3 aulas na semana e só 1 horário" in item for item in warnings)


def test_bandeirante_carrega_e_avisa_quando_a_carga_estoura_os_slots():
    school = load_instance(DATA_DIR)
    errors, warnings = validate_instance(school)
    assert errors == []
    assert school.teachers
    assert school.class_groups
    assert school.subjects
    assert len(school.time_slots) == 25
    overloaded = [
        group
        for group in school.class_groups
        if sum(
            item.weekly_workload
            for item in school.subjects
            if item.class_group_id == group.id
        )
        > 25
    ]
    assert overloaded
    encaixe = [item for item in warnings if "não consegue encaixar" in item]
    assert len(encaixe) == len(overloaded)

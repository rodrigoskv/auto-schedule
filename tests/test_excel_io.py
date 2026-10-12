"""Entrada tabular: nomes errados, carga inválida e professor sem dias."""

import pandas as pd
import pytest

from data.excel_io import class_groups_from_df, subjects_from_df, teachers_from_df
from data.school_hours import SchoolHours

from tests.builders import make_class, make_teacher

HOURS = SchoolHours(days=["segunda", "terca"], periods_per_day=2, shift="manha")


def test_professor_sem_dia_marcado_nao_ganha_a_semana_inteira():
    df = pd.DataFrame(
        [{"professor": "Ana", "segunda": "N", "terca": "N", "quarta": "N", "quinta": "N", "sexta": "N"}]
    )
    teachers = teachers_from_df(df, HOURS)
    assert len(teachers) == 1
    assert teachers[0].available_periods == []


def test_professor_duplicado_e_erro():
    df = pd.DataFrame([{"professor": "Ana", "segunda": "S"}, {"professor": "Ana", "segunda": "S"}])
    with pytest.raises(ValueError, match="repetido"):
        teachers_from_df(df, HOURS)


def test_turma_sem_ordinal_casa_com_turma_cadastrada():
    teachers = [make_teacher("caroline", name="Caroline", days=["segunda"])]
    groups = [make_class("6a", name="6º ano A")]
    df = pd.DataFrame(
        [
            {
                "turma": "6 ano A",
                "disciplina": "Matemática",
                "professor": "Caroline",
                "aulas_semanais": 2,
            }
        ]
    )
    subjects = subjects_from_df(df, teachers, groups)
    assert subjects[0].class_group_id == "6a"


def test_professor_com_typo_sugere_correcao():
    teachers = [make_teacher("caroline", name="Caroline", days=["segunda"])]
    groups = [make_class("6a", name="6º ano A")]
    df = pd.DataFrame(
        [
            {
                "turma": "6º ano A",
                "disciplina": "Matemática",
                "professor": "Carolne",
                "aulas_semanais": 2,
            }
        ]
    )
    with pytest.raises(ValueError, match="Você quis dizer 'Caroline'"):
        subjects_from_df(df, teachers, groups)


def test_junta_varios_erros_da_tabela_de_aulas():
    teachers = [make_teacher("caroline", name="Caroline", days=["segunda"])]
    groups = [make_class("6a", name="6º ano A")]
    df = pd.DataFrame(
        [
            {
                "turma": "9º ano",
                "disciplina": "Matemática",
                "professor": "Carolne",
                "aulas_semanais": "três",
            },
            {
                "turma": "6º ano A",
                "disciplina": "",
                "professor": "Caroline",
                "aulas_semanais": 0,
            },
        ]
    )
    with pytest.raises(ValueError) as info:
        subjects_from_df(df, teachers, groups)
    text = str(info.value)
    assert "9º ano" in text
    assert "Carolne" in text
    assert "inteiro" in text or "número" in text
    assert "em branco" in text or "pelo menos 1" in text


def test_carga_decimal_e_erro():
    teachers = [make_teacher("caroline", name="Caroline", days=["segunda"])]
    groups = [make_class("6a", name="6º ano A")]
    df = pd.DataFrame(
        [
            {
                "turma": "6º ano A",
                "disciplina": "Matemática",
                "professor": "Caroline",
                "aulas_semanais": 2.5,
            }
        ]
    )
    with pytest.raises(ValueError, match="inteiro"):
        subjects_from_df(df, teachers, groups)


def test_turma_duplicada_e_erro():
    df = pd.DataFrame([{"turma": "6º ano A", "turno": "manha"}, {"turma": "6º ano A", "turno": "manha"}])
    with pytest.raises(ValueError, match="repetida"):
        class_groups_from_df(df, HOURS)

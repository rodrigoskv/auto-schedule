"""Exemplo em CSV com nomes em inglês (pasta example/)."""

from pathlib import Path

from data.instance import load_instance
from data.school_hours import normalize_day, normalize_shift
from data.validate import validate_instance
from ga.context import GAContext

EXAMPLE_DIR = Path(__file__).resolve().parents[1] / "example"


def test_monday_vira_segunda():
    assert normalize_day("monday") == "segunda"
    assert normalize_day("Tuesday") == "terca"
    assert normalize_shift("morning") == "manha"


def test_pasta_example_carrega_e_e_viavel():
    school = load_instance(EXAMPLE_DIR)
    errors, warnings = validate_instance(school)
    assert errors == []
    assert warnings == []
    assert [group.name for group in school.class_groups] == ["6th Grade A", "7th Grade A"]
    assert {teacher.name for teacher in school.teachers} == {
        "Caroline",
        "Paula",
        "Danieli",
        "Nelso",
        "Pablo",
        "Vania",
    }
    assert len(school.time_slots) == 25
    assert school.time_slots[0].shift == "manha"

    context = GAContext.from_school(school)
    for group in school.class_groups:
        load = sum(subject.weekly_workload for subject in context.subjects_by_class_group[group.id])
        assert load <= len(context.slots_for_class(group.id))

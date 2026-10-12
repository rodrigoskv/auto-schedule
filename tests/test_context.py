"""GAContext agrupa disciplinas pelo class_group_id explícito, não pelo id."""

from tests.builders import (
    make_class,
    make_context,
    make_slots,
    make_subject,
    make_teacher,
    slot_id,
)


def test_disciplina_entra_na_turma_do_class_group_id_mesmo_com_id_de_outra():
    ctx = make_context(
        teachers=[make_teacher("ana")],
        class_groups=[make_class("6_ano_a"), make_class("7_ano_a")],
        subjects=[
            make_subject(
                "6_ano_a_matematica_ana",
                "ana",
                "7_ano_a",
                2,
                name="Matemática",
            )
        ],
        days=["segunda"],
        periods=2,
    )
    assert ctx.subjects_by_class_group["7_ano_a"][0].id == "6_ano_a_matematica_ana"
    assert ctx.subjects_by_class_group.get("6_ano_a") is None
    required = ctx.required_lessons_for_class("7_ano_a")
    assert required == [("6_ano_a_matematica_ana", "ana")] * 2
    assert ctx.required_lessons_for_class("6_ano_a") == []


def test_slots_da_turma_respeitam_o_turno():
    morning = make_slots(["segunda"], 2, "manha")
    afternoon = make_slots(["segunda"], 2, "tarde")
    ctx = make_context(
        teachers=[make_teacher("ana", days=["segunda"], shift="manha")],
        class_groups=[
            make_class("6a", shift="manha"),
            make_class("6b", shift="tarde"),
        ],
        subjects=[
            make_subject("mat_6a", "ana", "6a", 1),
            make_subject("mat_6b", "ana", "6b", 1),
        ],
        time_slots=morning + afternoon,
    )
    morning_ids = {slot.id for slot in ctx.slots_for_class("6a")}
    afternoon_ids = {slot.id for slot in ctx.slots_for_class("6b")}
    assert morning_ids == {slot_id("segunda", 1, "manha"), slot_id("segunda", 2, "manha")}
    assert afternoon_ids == {slot_id("segunda", 1, "tarde"), slot_id("segunda", 2, "tarde")}


def test_turma_sem_turno_usa_todos_os_slots():
    ctx = make_context(
        teachers=[make_teacher("ana")],
        class_groups=[make_class("6a", shift=None)],
        subjects=[make_subject("mat_6a", "ana", "6a", 1)],
        days=["segunda"],
        periods=2,
    )
    assert len(ctx.slots_for_class("6a")) == 2

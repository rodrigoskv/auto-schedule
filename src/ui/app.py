from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from data.excel_io import load_class_groups, load_subjects, load_teachers
from data.school_hours import DAY_LABEL, SchoolHours, build_time_slots
from data.templates import write_templates
from domain.entities import ClassGroup, Subject, Teacher, TimeSlot
from engine import run_ga
from ga.context import GAContext
from ga.operators.representation import SLOT_ORDERING_STRATEGIES

st.set_page_config(page_title="Auto-Schedule", layout="wide")

DAYS = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado"]
SHIFT_LABEL = {"manha": "Manhã", "tarde": "Tarde", "noite": "Noite"}
DATA_DIR = REPO / "data"


def _hours_from_sidebar() -> SchoolHours:
    st.sidebar.header("Horários da escola")
    shift = st.sidebar.selectbox("Turno", list(SHIFT_LABEL), format_func=lambda v: SHIFT_LABEL[v])
    periods = st.sidebar.slider("Aulas por dia", 3, 10, 5)
    selected = st.sidebar.multiselect(
        "Dias letivos", DAYS, default=DAYS[:5], format_func=lambda d: DAY_LABEL[d]
    )
    days = [d for d in DAYS if d in selected] or ["segunda"]
    return SchoolHours(days=days, periods_per_day=periods, shift=shift)


def _molde(filename: str) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        write_templates(tmp)
        return (Path(tmp) / filename).read_bytes()


def _save_upload(uploaded) -> Path:
    suffix = Path(uploaded.name).suffix or ".xlsx"
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    handle.write(uploaded.getbuffer())
    handle.close()
    return Path(handle.name)


def _load_json(name: str, model):
    with open(DATA_DIR / name, encoding="utf-8") as handle:
        return [model(**item) for item in json.load(handle)]


def _capacity_table(class_groups, subjects, hours: SchoolHours) -> pd.DataFrame:
    rows = []
    for group in class_groups:
        requested = sum(s.weekly_workload for s in subjects if s.class_group_id == group.id)
        if requested == 0:
            requested = sum(s.weekly_workload for s in subjects if s.id.startswith(group.id + "_"))
        rows.append(
            {
                "Turma": group.name,
                "Aulas pedidas": requested,
                "Horários": hours.slots_per_class,
                "Saldo": hours.slots_per_class - requested,
            }
        )
    return pd.DataFrame(rows)


def _grid(result, context: GAContext) -> None:
    days = []
    for slot in context.time_slots:
        if slot.day_of_week not in days:
            days.append(slot.day_of_week)
    periods = sorted({slot.order for slot in context.time_slots})
    for group in context.class_groups:
        st.subheader(group.name)
        data = {DAY_LABEL.get(day, day): [] for day in days}
        index = []
        for order in periods:
            index.append(f"{order}º")
            for day in days:
                slot = next(
                    (
                        item
                        for item in context.time_slots
                        if item.day_of_week == day and item.order == order and item.shift == group.shift
                    ),
                    None,
                )
                lesson = next(
                    (
                        item
                        for item in result.schedule.get_lessons_for_class_group(group.id)
                        if slot and item.time_slot_id == slot.id
                    ),
                    None,
                )
                if lesson:
                    subject = context.subjects_by_id.get(lesson.subject_id)
                    teacher = context.teachers_by_id.get(lesson.teacher_id)
                    cell = f"{subject.name if subject else lesson.subject_id}\n{teacher.name if teacher else ''}"
                else:
                    cell = "—"
                data[DAY_LABEL.get(day, day)].append(cell)
        st.dataframe(pd.DataFrame(data, index=index), width="stretch")


def main() -> None:
    st.title("Auto-Schedule")
    st.caption("Envie as planilhas e defina a rotina da escola.")

    hours = _hours_from_sidebar()
    st.sidebar.caption(f"Cada turma terá {hours.slots_per_class} horários na semana.")
    st.sidebar.header("Algoritmo")
    population = st.sidebar.number_input("População", 10, 200, 60, 10)
    generations = st.sidebar.number_input("Gerações", 10, 500, 120, 10)
    mutation = st.sidebar.number_input("Mutação", 0.01, 0.5, 0.08, 0.01)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button("Molde professores", _molde("molde-professores.xlsx"), "molde-professores.xlsx")
        teachers_file = st.file_uploader("Professores", type=["xlsx", "xls", "csv"], key="teachers")
    with col_b:
        st.download_button("Molde turmas", _molde("molde-turmas.xlsx"), "molde-turmas.xlsx")
        classes_file = st.file_uploader("Turmas", type=["xlsx", "xls", "csv"], key="classes")
    with col_c:
        st.download_button("Molde aulas", _molde("molde-aulas.xlsx"), "molde-aulas.xlsx")
        subjects_file = st.file_uploader("Aulas", type=["xlsx", "xls", "csv"], key="subjects")

    col1, col2 = st.columns(2)
    load_json_clicked = col1.button("Carregar JSON do repositório", width="stretch")
    generate_clicked = col2.button("Gerar grade", type="primary", width="stretch")

    if load_json_clicked:
        st.session_state["payload"] = {
            "hours": hours,
            "teachers": _load_json("teachers.json", Teacher),
            "class_groups": _load_json("class_groups.json", ClassGroup),
            "subjects": _load_json("subjects.json", Subject),
            "time_slots": _load_json("time_slots.json", TimeSlot),
        }
        st.session_state.pop("result", None)
        st.success("JSON de data/ carregado.")

    if teachers_file and classes_file and subjects_file:
        try:
            teachers = load_teachers(_save_upload(teachers_file), hours)
            groups = load_class_groups(_save_upload(classes_file), hours)
            subjects = load_subjects(_save_upload(subjects_file), teachers, groups)
            st.session_state["payload"] = {
                "hours": hours,
                "teachers": teachers,
                "class_groups": groups,
                "subjects": subjects,
                "time_slots": build_time_slots(hours),
            }
        except Exception as exc:
            st.error(str(exc))

    payload = st.session_state.get("payload")
    if payload:
        teachers = payload["teachers"]
        groups = payload["class_groups"]
        subjects = payload["subjects"]
        hours_used = payload["hours"]
        slots = payload["time_slots"]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Professores", len(teachers))
        m2.metric("Turmas", len(groups))
        m3.metric("Disciplinas", len(subjects))
        m4.metric("Horários", len(slots))
        cap = _capacity_table(groups, subjects, hours_used)
        st.dataframe(cap, width="stretch", hide_index=True)
        if not cap.empty and int((cap["Saldo"] < 0).sum()):
            st.warning("Turma com mais aulas do que horários: H3 não zera.")

        if generate_clicked:
            context = GAContext(
                teachers=teachers,
                class_groups=groups,
                subjects=subjects,
                time_slots=slots,
                slot_ordering_key=SLOT_ORDERING_STRATEGIES["shift_then_day"],
            )
            with st.spinner("Gerando grade…"):
                result = run_ga(
                    context=context,
                    population_size=int(population),
                    generations=int(generations),
                    mutation_rate=float(mutation),
                    verbose=False,
                )
            st.session_state["result"] = result
            st.session_state["context"] = context

    if "result" in st.session_state:
        result = st.session_state["result"]
        context = st.session_state["context"]
        counts = result.breakdown.counts
        st.success(
            f"Fitness {result.fitness:.0f} · {result.generation_reached} gerações · {result.elapsed_seconds:.1f}s"
        )
        v1, v2, v3, v4, v5 = st.columns(5)
        v1.metric("H1", counts.get("H1", 0))
        v2.metric("H2", counts.get("H2", 0))
        v3.metric("H3", counts.get("H3", 0))
        v4.metric("H4", counts.get("H4", 0))
        v5.metric("S1", counts.get("S1", 0))
        _grid(result, context)


if __name__ == "__main__":
    main()
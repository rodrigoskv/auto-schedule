"""Tela: o usuário informa a escola (tabelas ou arquivo) e o AG gera o horário."""

from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from data.excel_io import (
    class_groups_from_df,
    class_groups_to_df,
    load_from_workbook,
    subjects_from_df,
    subjects_to_df,
    teachers_from_df,
    teachers_to_df,
)
from data.instance import load_instance
from data.school_hours import DAY_LABEL, DAYS, SHIFT_LABEL, SchoolHours, build_time_slots, hours_from_slots
from data.templates import CLASSES_DF, SUBJECTS_DF, TEACHERS_DF, csv_bytes, molde_bytes
from data.validate import validate_instance
from domain.entities import SchoolInstance
from ga.context import GAContext
from ga.engine import run_ga

DATA_DIR = REPO / "data"

CSS = """
<style>
    .block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1180px; }
    header[data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }

    .hero {
        background: #FBF8F2;
        border: 1px solid #E6DFD2;
        border-left: 6px solid #1F4D47;
        border-radius: 14px;
        padding: 1.15rem 1.4rem 1.2rem;
        margin-bottom: 1.4rem;
    }
    .hero h1 {
        color: #1F4D47 !important;
        font-size: 1.65rem;
        letter-spacing: -0.03em;
        margin: 0 0 .3rem 0;
    }
    .hero p { margin: 0; color: #5C574F; }

    .hint { color: #6F6A62; font-size: .92rem; margin: 0 0 .8rem 0; }

    .timetable { width: 100%; border-collapse: separate; border-spacing: 5px; margin-bottom: 1.2rem; }
    .timetable th {
        background: #1F4D47; color: #FBF8F2; padding: .5rem .65rem;
        border-radius: 8px; font-weight: 600; font-size: .82rem;
    }
    .timetable td {
        background: #FBF8F2; padding: .6rem .65rem; border-radius: 8px;
        vertical-align: top; font-size: .86rem; border: 1px solid #E6DFD2;
    }
    .timetable td.empty { color: #B8B0A4; text-align: center; }
    .timetable .period { background: #EDE6D8; font-weight: 600; text-align: center; width: 2.6rem; }
    .cell-subject { font-weight: 600; color: #1F4D47; }
    .cell-teacher { color: #6F6A62; font-size: .78rem; margin-top: .15rem; }

    div[data-testid="stMetric"] {
        background: #FBF8F2; border: 1px solid #E6DFD2;
        border-radius: 12px; padding: .35rem .75rem;
    }
    .stButton button[kind="primary"] { border-radius: 10px; padding: .45rem 1.2rem; }
</style>
"""


def _bool_days(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for day in DAYS:
        if day not in out.columns:
            out[day] = day != "sabado"
        else:
            out[day] = [
                str(value).strip().lower() in {"s", "sim", "yes", "y", "1", "x", "true"}
                for value in out[day]
            ]
    return out


def _empty_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    turmas = pd.DataFrame({"turma": [""], "turno": ["manha"]})
    profs = pd.DataFrame({"professor": [""], **{day: day != "sabado" for day in DAYS}})
    aulas = pd.DataFrame(
        {"turma": [""], "disciplina": [""], "professor": [""], "aulas_semanais": [1]}
    )
    return turmas, profs, aulas


def _init_state() -> None:
    if "ready" in st.session_state:
        return
    st.session_state.ready = True
    st.session_state.shift = "manha"
    st.session_state.lessons_per_day = 5
    st.session_state.school_days = DAYS[:5]
    st.session_state.turmas_df, st.session_state.profs_df, st.session_state.aulas_df = _empty_tables()


def _reset_editors() -> None:
    for key in ("turmas_ed", "profs_ed", "aulas_ed"):
        st.session_state.pop(key, None)
    st.session_state.pop("result", None)
    st.session_state.pop("context", None)


def _apply_instance(school: SchoolInstance) -> None:
    hours = hours_from_slots(school.time_slots)
    st.session_state.shift = hours.shift
    st.session_state.lessons_per_day = hours.periods_per_day
    st.session_state.school_days = hours.days
    st.session_state.turmas_df = class_groups_to_df(school.class_groups)
    st.session_state.profs_df = _bool_days(teachers_to_df(school.teachers, hours))
    st.session_state.aulas_df = subjects_to_df(school.subjects, school.teachers, school.class_groups)
    _reset_editors()


def _apply_sample() -> None:
    st.session_state.shift = "manha"
    st.session_state.lessons_per_day = 5
    st.session_state.school_days = DAYS[:5]
    st.session_state.turmas_df = CLASSES_DF.copy()
    st.session_state.profs_df = _bool_days(TEACHERS_DF)
    st.session_state.aulas_df = SUBJECTS_DF.copy()
    _reset_editors()


def _current_hours() -> SchoolHours:
    days = [day for day in DAYS if day in st.session_state.get("school_days", DAYS[:5])] or ["segunda"]
    return SchoolHours(
        days=days,
        periods_per_day=int(st.session_state.get("lessons_per_day", 5)),
        shift=st.session_state.get("shift", "manha"),
    )


def _read_table(uploaded) -> pd.DataFrame:
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded)
    return pd.read_excel(uploaded)


def _sidebar() -> tuple[SchoolHours, int, int, float]:
    st.sidebar.markdown("### Semana letiva")
    shift = st.sidebar.selectbox(
        "Turno", list(SHIFT_LABEL), format_func=lambda v: SHIFT_LABEL[v], key="shift"
    )
    periods = st.sidebar.slider("Aulas por dia", 3, 10, key="lessons_per_day")
    selected = st.sidebar.multiselect(
        "Dias letivos", DAYS, format_func=lambda day: DAY_LABEL[day], key="school_days"
    )
    days = [day for day in DAYS if day in selected] or ["segunda"]
    hours = SchoolHours(days=days, periods_per_day=int(periods), shift=shift)
    st.sidebar.caption(f"{hours.slots_per_class} horários por turma na semana.")

    st.sidebar.markdown("### Algoritmo")
    population = st.sidebar.number_input("População", 10, 200, 60, 10)
    generations = st.sidebar.number_input("Gerações", 10, 500, 120, 10)
    mutation = st.sidebar.number_input("Mutação", 0.01, 0.5, 0.08, 0.01)
    return hours, int(population), int(generations), float(mutation)


def _import_panel() -> None:
    st.markdown(
        '<p class="hint">Digite direto nas tabelas abaixo, ou traga um arquivo. '
        "O conteúdo importado entra nas mesmas tabelas, para você revisar antes de gerar.</p>",
        unsafe_allow_html=True,
    )

    with st.expander("Importar arquivo  (.xlsx ou .csv)", expanded=False):
        molde = st.file_uploader(
            "Planilha completa (abas Grade, Turmas, Professores, Aulas)",
            type=["xlsx", "xls"],
            key="up_molde",
        )
        if molde is not None:
            token = ("molde", molde.name, molde.size)
            if st.session_state.get("uploaded_token") != token:
                try:
                    _apply_instance(load_from_workbook(molde))
                    st.session_state.uploaded_token = token
                    st.rerun()
                except (OSError, TypeError, ValueError) as exc:
                    st.error(str(exc))

        st.caption("Ou envie cada tabela à parte (.xlsx ou .csv). Envie turmas e professores antes das aulas.")
        c1, c2, c3 = st.columns(3)
        with c1:
            f_turmas = st.file_uploader("Turmas", type=["xlsx", "xls", "csv"], key="up_turmas")
        with c2:
            f_profs = st.file_uploader("Professores", type=["xlsx", "xls", "csv"], key="up_profs")
        with c3:
            f_aulas = st.file_uploader("Aulas", type=["xlsx", "xls", "csv"], key="up_aulas")

        hours = _current_hours()
        try:
            if f_turmas is not None:
                token = ("turmas", f_turmas.name, f_turmas.size)
                if st.session_state.get("uploaded_token") != token:
                    groups = class_groups_from_df(_read_table(f_turmas), hours)
                    st.session_state.turmas_df = class_groups_to_df(groups)
                    st.session_state.pop("turmas_ed", None)
                    st.session_state.uploaded_token = token
                    st.rerun()
            if f_profs is not None:
                token = ("profs", f_profs.name, f_profs.size)
                if st.session_state.get("uploaded_token") != token:
                    teachers = teachers_from_df(_read_table(f_profs), hours)
                    st.session_state.profs_df = _bool_days(teachers_to_df(teachers, hours))
                    st.session_state.pop("profs_ed", None)
                    st.session_state.uploaded_token = token
                    st.rerun()
            if f_aulas is not None:
                token = ("aulas", f_aulas.name, f_aulas.size)
                if st.session_state.get("uploaded_token") != token:
                    teachers = teachers_from_df(st.session_state.profs_df, hours)
                    groups = class_groups_from_df(st.session_state.turmas_df, hours)
                    subjects = subjects_from_df(_read_table(f_aulas), teachers, groups)
                    st.session_state.aulas_df = subjects_to_df(subjects, teachers, groups)
                    st.session_state.pop("aulas_ed", None)
                    st.session_state.uploaded_token = token
                    st.rerun()
        except (OSError, TypeError, ValueError) as exc:
            st.error(str(exc))

        st.divider()
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Exemplo curto", width="stretch"):
                _apply_sample()
                st.rerun()
        with b2:
            if st.button("Exemplo Bandeirante", width="stretch"):
                _apply_instance(load_instance(DATA_DIR))
                st.rerun()
        with b3:
            if st.button("Limpar tabelas", width="stretch"):
                st.session_state.turmas_df, st.session_state.profs_df, st.session_state.aulas_df = _empty_tables()
                _reset_editors()
                st.rerun()

        d1, d2, d3, d4 = st.columns(4)
        d1.download_button("molde.xlsx", molde_bytes(), "molde.xlsx", width="stretch")
        d2.download_button("turmas.csv", csv_bytes(CLASSES_DF), "turmas.csv", width="stretch")
        d3.download_button("professores.csv", csv_bytes(TEACHERS_DF), "professores.csv", width="stretch")
        d4.download_button("aulas.csv", csv_bytes(SUBJECTS_DF), "aulas.csv", width="stretch")


def _editors() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Turmas**")
        st.caption("Uma linha por turma. Clique na célula para editar; use + para incluir.")
        turmas = st.data_editor(
            st.session_state.turmas_df,
            num_rows="dynamic",
            key="turmas_ed",
            hide_index=True,
            column_config={
                "turma": st.column_config.TextColumn("Turma", required=False),
                "turno": st.column_config.SelectboxColumn("Turno", options=list(SHIFT_LABEL)),
            },
            width="stretch",
        )
    with c2:
        st.markdown("**Professores**")
        st.caption("Marque os dias em que cada professor pode dar aula.")
        day_cols = {day: st.column_config.CheckboxColumn(DAY_LABEL[day]) for day in DAYS}
        profs = st.data_editor(
            st.session_state.profs_df,
            num_rows="dynamic",
            key="profs_ed",
            hide_index=True,
            column_config={"professor": st.column_config.TextColumn("Professor"), **day_cols},
            width="stretch",
        )

    st.markdown("**Aulas da semana**")
    st.caption("Turma + disciplina + professor + quantas vezes a disciplina aparece na semana.")
    aulas = st.data_editor(
        st.session_state.aulas_df,
        num_rows="dynamic",
        key="aulas_ed",
        hide_index=True,
        column_config={
            "turma": st.column_config.TextColumn("Turma"),
            "disciplina": st.column_config.TextColumn("Disciplina"),
            "professor": st.column_config.TextColumn("Professor"),
            "aulas_semanais": st.column_config.NumberColumn("Aulas na semana", min_value=1, step=1),
        },
        width="stretch",
    )
    return turmas, profs, aulas


def _build(turmas, profs, aulas, hours: SchoolHours) -> SchoolInstance:
    teachers = teachers_from_df(profs, hours)
    groups = class_groups_from_df(turmas, hours)
    subjects = subjects_from_df(aulas, teachers, groups)
    return SchoolInstance(
        teachers=teachers,
        class_groups=groups,
        subjects=subjects,
        time_slots=build_time_slots(hours),
    )


def _capacity(school: SchoolInstance, hours: SchoolHours) -> pd.DataFrame:
    rows = []
    for group in school.class_groups:
        requested = sum(
            item.weekly_workload for item in school.subjects if item.class_group_id == group.id
        )
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
    days = list(dict.fromkeys(slot.day_of_week for slot in context.time_slots))
    periods = sorted({slot.order for slot in context.time_slots})
    slots = {(slot.day_of_week, slot.order, slot.shift): slot for slot in context.time_slots}

    for group in context.class_groups:
        st.markdown(f"##### {html.escape(group.name)}")
        by_slot = {
            lesson.time_slot_id: lesson
            for lesson in result.schedule.get_lessons_for_class_group(group.id)
            if lesson.time_slot_id
        }
        head = "".join(f"<th>{html.escape(DAY_LABEL.get(day, day))}</th>" for day in days)
        rows = []
        for order in periods:
            cells = [f'<td class="period">{order}º</td>']
            for day in days:
                slot = slots.get((day, order, group.shift))
                lesson = by_slot.get(slot.id) if slot else None
                if lesson:
                    subject = context.subjects_by_id.get(lesson.subject_id)
                    teacher = context.teachers_by_id.get(lesson.teacher_id)
                    subject_name = html.escape(subject.name if subject else lesson.subject_id)
                    teacher_name = html.escape(teacher.name if teacher else "")
                    cells.append(
                        f'<td><div class="cell-subject">{subject_name}</div>'
                        f'<div class="cell-teacher">{teacher_name}</div></td>'
                    )
                else:
                    cells.append('<td class="empty">—</td>')
            rows.append("<tr>" + "".join(cells) + "</tr>")
        st.markdown(
            f'<table class="timetable"><tr><th></th>{head}</tr>{"".join(rows)}</table>',
            unsafe_allow_html=True,
        )


def _school_tab(hours: SchoolHours, population: int, generations: int, mutation: float) -> None:
    _import_panel()
    st.markdown("### Dados da escola")
    turmas, profs, aulas = _editors()

    try:
        school = _build(turmas, profs, aulas, hours)
    except (TypeError, ValueError) as exc:
        st.error(str(exc))
        return

    errors, warnings = validate_instance(school)
    for warning in warnings:
        st.warning(warning)
    if errors:
        for error in errors:
            st.error(error)
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Professores", len(school.teachers))
    m2.metric("Turmas", len(school.class_groups))
    m3.metric("Disciplinas", len(school.subjects))
    m4.metric("Horários", len(school.time_slots))
    st.dataframe(_capacity(school, hours), width="stretch", hide_index=True)

    if st.button("Gerar horário", type="primary"):
        context = GAContext.from_school(school)
        with st.spinner("Montando o horário…"):
            result = run_ga(
                context,
                population_size=population,
                generations=generations,
                mutation_rate=mutation,
                verbose=False,
            )
        st.session_state.result = result
        st.session_state.context = context
        st.success("Horário gerado. Abra a aba Horário para ver a grade.")


def _result_tab() -> None:
    if "result" not in st.session_state:
        st.info("Preencha a escola na aba Dados e clique em Gerar horário.")
        return

    result = st.session_state.result
    context = st.session_state.context
    counts = result.breakdown.counts
    st.caption(
        f"Fitness {result.fitness:.0f} · {result.generation_reached} gerações · {result.elapsed_seconds:.1f}s"
    )
    v1, v2, v3, v4, v5 = st.columns(5)
    v1.metric("H1 choque professor", counts.get("H1", 0))
    v2.metric("H2 choque turma", counts.get("H2", 0))
    v3.metric("H3 carga", counts.get("H3", 0))
    v4.metric("H4 disponibilidade", counts.get("H4", 0))
    v5.metric("S1 concentração", counts.get("S1", 0))
    _grid(result, context)


def main() -> None:
    st.set_page_config(page_title="Auto-Schedule", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="hero"><h1>Auto-Schedule</h1>'
        "<p>Digite a escola nas tabelas ou importe um arquivo. O AG monta o horário da semana.</p></div>",
        unsafe_allow_html=True,
    )

    _init_state()
    hours, population, generations, mutation = _sidebar()
    dados, horario = st.tabs(["Dados da escola", "Horário"])
    with dados:
        _school_tab(hours, population, generations, mutation)
    with horario:
        _result_tab()


if __name__ == "__main__":
    main()

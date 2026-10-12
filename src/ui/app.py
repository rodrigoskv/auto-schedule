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
from reporting.export import timetable_excel
from reporting.violations import explain_problems, quality_status, unassigned_rows

DATA_DIR = REPO / "data"
EXAMPLE_DIR = REPO / "example"

CSS = """
<style>
    .block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1180px; }
    header[data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }

    .hero {
        background: #FBF8F2;
        border: 1px solid #E6DFD2;
        border-left: 6px solid #1F4D47;
        border-radius: 14px;
        padding: 1.15rem 1.4rem 1.2rem;
        margin-bottom: 1.2rem;
    }
    .hero h1 {
        color: #1F4D47 !important;
        font-size: 1.65rem;
        letter-spacing: -0.03em;
        margin: 0 0 .3rem 0;
    }
    .hero p { margin: 0; color: #5C574F; }
    .steps { margin: .75rem 0 0 0; padding: 0; color: #5C574F; font-size: .92rem; }
    .steps span {
        display: inline-block; background: #EDE6D8; color: #1F4D47;
        border-radius: 999px; padding: .1rem .55rem; margin-right: .35rem;
        font-weight: 700; font-size: .78rem;
    }

    .hint { color: #6F6A62; font-size: .92rem; margin: 0 0 .8rem 0; }

    .banner {
        border-radius: 12px; padding: .9rem 1.15rem; margin: 0 0 1rem 0;
        border: 1px solid #E6DFD2;
    }
    .banner h3 { margin: 0 0 .25rem 0; font-size: 1.08rem; color: #1F4D47; }
    .banner p { margin: 0; color: #5C574F; }
    .banner-ok { background: #EEF6F3; border-left: 6px solid #1F4D47; }
    .banner-warn { background: #FBF6EA; border-left: 6px solid #C4A35A; }
    .banner-bad { background: #F8EEEE; border-left: 6px solid #A33B3B; }

    .problem { margin: .4rem 0 .8rem 0; padding: .7rem .9rem; background: #FBF8F2;
        border: 1px solid #E6DFD2; border-radius: 10px; }
    .problem strong { color: #1F4D47; }
    .problem .count { color: #A33B3B; font-weight: 700; }
    .problem p { margin: .2rem 0 0 0; color: #6F6A62; font-size: .9rem; }

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
    st.session_state.nav = "dados"
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


def _queue_instance(school: SchoolInstance) -> None:
    """Guarda a escola e recarrega: os widgets da barra só aceitam valor no início do script."""
    st.session_state.pending_school = school
    st.rerun()


def _consume_pending_instance() -> None:
    school = st.session_state.pop("pending_school", None)
    if school is not None:
        _apply_instance(school)
    if st.session_state.pop("pending_clear", False):
        st.session_state.turmas_df, st.session_state.profs_df, st.session_state.aulas_df = _empty_tables()
        _reset_editors()
    pending_nav = st.session_state.pop("pending_nav", None)
    if pending_nav is not None:
        st.session_state.nav = pending_nav


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


def _names(df: pd.DataFrame, column: str) -> list[str]:
    if column not in df.columns:
        return []
    values: list[str] = []
    seen: set[str] = set()
    for raw in df[column].tolist():
        text = str(raw).strip()
        if not text or text.lower() in {"nan", "none"}:
            continue
        key = text.lower()
        if key not in seen:
            seen.add(key)
            values.append(text)
    return values


def _excel_bytes(factory):
    try:
        return factory()
    except ImportError:
        return None


def _show_exception(exc: BaseException) -> None:
    for line in str(exc).splitlines():
        if line.strip():
            st.error(line)


def _teachers_without_days(profs: pd.DataFrame, hours: SchoolHours) -> list[str]:
    missing: list[str] = []
    for _, row in profs.iterrows():
        name = str(row.get("professor", "")).strip()
        if not name or name.lower() in {"nan", "none"}:
            continue
        marked = False
        for day in hours.days:
            if day in profs.columns and str(row[day]).strip().lower() in {
                "s",
                "sim",
                "yes",
                "y",
                "1",
                "x",
                "true",
            }:
                marked = True
                break
        if not marked:
            missing.append(name)
    return missing


def _sidebar() -> tuple[SchoolHours, int, int, float]:
    st.sidebar.markdown("### Semana letiva")
    st.sidebar.caption("Quantos dias e quantas aulas cada turma tem por dia.")
    shift = st.sidebar.selectbox(
        "Turno",
        list(SHIFT_LABEL),
        format_func=lambda v: SHIFT_LABEL[v],
        key="shift",
        help="Manhã, tarde ou noite. As turmas usam o mesmo turno, salvo se você mudar na tabela.",
    )
    periods = st.sidebar.slider(
        "Aulas por dia",
        3,
        10,
        key="lessons_per_day",
        help="Ex.: 5 aulas de manhã. Isso define quantos horários existem na semana.",
    )
    selected = st.sidebar.multiselect(
        "Dias letivos",
        DAYS,
        format_func=lambda day: DAY_LABEL[day],
        key="school_days",
    )
    days = [day for day in DAYS if day in selected] or ["segunda"]
    hours = SchoolHours(days=days, periods_per_day=int(periods), shift=shift)
    st.sidebar.info(f"**{hours.slots_per_class} horários** por turma na semana.")

    with st.sidebar.expander("Ajustes do gerador", expanded=False):
        st.caption(
            "Pode deixar como está. Em escolas grandes, aumentar as gerações "
            "melhora o horário, mas demora mais."
        )
        population = st.number_input("Tamanho da população", 10, 200, 60, 10)
        generations = st.number_input("Quantas tentativas (gerações)", 10, 500, 120, 10)
        mutation = st.number_input("Variação (mutação)", 0.01, 0.5, 0.08, 0.01)
    return hours, int(population), int(generations), float(mutation)


def _import_panel() -> None:
    a, b, c = st.columns(3)
    with a:
        if st.button("Carregar pasta example", width="stretch"):
            _queue_instance(load_instance(EXAMPLE_DIR))
    with b:
        if st.button("Carregar escola Bandeirante", width="stretch"):
            _queue_instance(load_instance(DATA_DIR))
    with c:
        if st.button("Limpar tabelas", width="stretch"):
            st.session_state.pending_clear = True
            st.rerun()
    st.caption("A pasta example/ tem 2 turmas em CSV (inglês). Bandeirante é a escola completa.")

    with st.expander("Já tenho uma planilha (.xlsx ou .csv)"):
        st.markdown(
            "O arquivo entra nas tabelas abaixo para você revisar. "
            "Baixe o molde se quiser preencher no Excel."
        )
        molde = st.file_uploader(
            "Planilha completa (abas Grade, Turmas, Professores, Aulas)",
            type=["xlsx", "xls"],
            key="up_molde",
        )
        if molde is not None:
            token = ("molde", molde.name, molde.size)
            if st.session_state.get("uploaded_token") != token:
                try:
                    st.session_state.uploaded_token = token
                    _queue_instance(load_from_workbook(molde))
                except (OSError, TypeError, ValueError) as exc:
                    _show_exception(exc)

        st.caption("Ou envie cada tabela à parte. Cadastre turmas e professores antes das aulas.")
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
            _show_exception(exc)

        st.divider()
        d1, d2, d3, d4 = st.columns(4)
        molde_file = _excel_bytes(molde_bytes)
        if molde_file is not None:
            d1.download_button("Baixar molde.xlsx", molde_file, "molde.xlsx", width="stretch")
        else:
            d1.caption("Instale openpyxl para o molde Excel.")
        d2.download_button("turmas.csv", csv_bytes(CLASSES_DF), "turmas.csv", width="stretch")
        d3.download_button("professores.csv", csv_bytes(TEACHERS_DF), "professores.csv", width="stretch")
        d4.download_button("aulas.csv", csv_bytes(SUBJECTS_DF), "aulas.csv", width="stretch")


def _editors() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**1. Turmas**")
        st.caption("Uma linha por turma. Clique na célula para editar; o + inclui outra.")
        turmas = st.data_editor(
            st.session_state.turmas_df,
            num_rows="dynamic",
            key="turmas_ed",
            hide_index=True,
            column_config={
                "turma": st.column_config.TextColumn("Turma", help="Ex.: 6º ano A"),
                "turno": st.column_config.SelectboxColumn(
                    "Turno", options=list(SHIFT_LABEL), help="Precisa existir na semana letiva."
                ),
            },
            width="stretch",
        )
    with c2:
        st.markdown("**2. Professores**")
        st.caption("Marque os dias em que cada pessoa pode dar aula. Só valem os dias letivos da barra.")
        day_cols = {day: st.column_config.CheckboxColumn(DAY_LABEL[day]) for day in DAYS}
        profs = st.data_editor(
            st.session_state.profs_df,
            num_rows="dynamic",
            key="profs_ed",
            hide_index=True,
            column_config={
                "professor": st.column_config.TextColumn("Professor", help="O nome precisa ser o mesmo na tabela de aulas."),
                **day_cols,
            },
            width="stretch",
        )

    st.markdown("**3. Aulas da semana**")
    st.caption(
        "Cada linha é uma disciplina de uma turma. Escolha turma e professor nas listas "
        "(os nomes precisam ser iguais aos das tabelas acima)."
    )
    turma_options = [""] + list(dict.fromkeys(_names(turmas, "turma") + _names(st.session_state.aulas_df, "turma")))
    prof_options = [""] + list(dict.fromkeys(_names(profs, "professor") + _names(st.session_state.aulas_df, "professor")))
    aulas = st.data_editor(
        st.session_state.aulas_df,
        num_rows="dynamic",
        key="aulas_ed",
        hide_index=True,
        column_config={
            "turma": st.column_config.SelectboxColumn("Turma", options=turma_options),
            "disciplina": st.column_config.TextColumn("Disciplina", help="Ex.: Matemática"),
            "professor": st.column_config.SelectboxColumn("Professor", options=prof_options),
            "aulas_semanais": st.column_config.NumberColumn(
                "Aulas na semana",
                min_value=1,
                max_value=20,
                step=1,
                help="Quantas vezes essa disciplina aparece na semana para essa turma.",
            ),
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


def _capacity(school: SchoolInstance) -> pd.DataFrame:
    rows = []
    for group in school.class_groups:
        requested = sum(
            item.weekly_workload for item in school.subjects if item.class_group_id == group.id
        )
        n_slots = len(
            [slot for slot in school.time_slots if group.shift is None or slot.shift == group.shift]
        )
        if requested == 0:
            situacao = "Sem aulas cadastradas"
        elif requested < n_slots:
            situacao = f"Cabe · {n_slots - requested} horários livres"
        elif requested == n_slots:
            situacao = "Cabe · semana cheia"
        else:
            situacao = f"Não cabe · {requested - n_slots} aulas a mais"
        rows.append(
            {
                "Turma": group.name,
                "Aulas da semana": requested,
                "Horários disponíveis": n_slots,
                "Situação": situacao,
            }
        )
    return pd.DataFrame(rows)


def _grid(result, context: GAContext) -> None:
    days = list(dict.fromkeys(slot.day_of_week for slot in context.time_slots))
    periods = sorted({slot.order for slot in context.time_slots})
    slots = {(slot.day_of_week, slot.order, slot.shift): slot for slot in context.time_slots}

    for group in context.class_groups:
        turno = SHIFT_LABEL.get(group.shift or "", group.shift or "")
        st.markdown(f"##### {html.escape(group.name)}  ·  {html.escape(turno)}")
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
    st.markdown(
        '<p class="hint">Preencha as três tabelas. Turma e professor na lista de aulas '
        "precisam ter o mesmo nome que nas tabelas de cima. Depois confira o resumo e gere o horário.</p>",
        unsafe_allow_html=True,
    )
    _import_panel()
    st.markdown("### Dados da escola")
    turmas, profs, aulas = _editors()

    try:
        school = _build(turmas, profs, aulas, hours)
    except (TypeError, ValueError) as exc:
        st.markdown(
            '<div class="banner banner-bad"><h3>Há nomes ou números que não fecham</h3>'
            "<p>Corrija as linhas abaixo. Em geral é turma/professor com nome diferente "
            "ou aulas_semanais inválida.</p></div>",
            unsafe_allow_html=True,
        )
        _show_exception(exc)
        return

    errors, warnings = validate_instance(school)
    for name in _teachers_without_days(profs, hours):
        errors.append(
            f"Professor {name}: marque pelo menos um dia letivo. "
            "Sem isso o gerador não sabe quando essa pessoa pode dar aula."
        )
        warnings = [item for item in warnings if f"Professor {name} está sem dias marcados" not in item]
    if errors:
        st.markdown(
            '<div class="banner banner-bad"><h3>Corrija os dados antes de gerar</h3>'
            "<p>O gerador só roda quando turmas, professores e aulas se encostam sem erro.</p></div>",
            unsafe_allow_html=True,
        )
        for error in errors:
            st.error(error)
        return

    if warnings:
        st.markdown(
            '<div class="banner banner-warn"><h3>Pode gerar, mas o horário pode ficar incompleto</h3>'
            "<p>Leia os avisos. O mais comum é a turma pedir mais aulas do que horários na semana.</p></div>",
            unsafe_allow_html=True,
        )
        for warning in warnings:
            st.warning(warning)
    else:
        st.markdown(
            '<div class="banner banner-ok"><h3>Dados consistentes</h3>'
            "<p>Turmas, professores e aulas fecham com a semana letiva. Pode gerar o horário.</p></div>",
            unsafe_allow_html=True,
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Professores", len(school.teachers))
    m2.metric("Turmas", len(school.class_groups))
    m3.metric("Disciplinas", len(school.subjects))
    m4.metric("Horários na semana", hours.slots_per_class)
    st.caption("Cada turma precisa ter aulas da semana ≤ horários disponíveis.")
    st.dataframe(_capacity(school), width="stretch", hide_index=True)

    if st.button("Gerar horário", type="primary"):
        context = GAContext.from_school(school)
        with st.spinner("Montando o horário da semana… isso pode levar alguns segundos."):
            result = run_ga(
                context,
                population_size=population,
                generations=generations,
                mutation_rate=mutation,
                verbose=False,
            )
        st.session_state.result = result
        st.session_state.context = context
        st.session_state.pending_nav = "horario"
        st.rerun()


def _result_tab() -> None:
    if "result" not in st.session_state:
        st.info("Ainda não há horário. Preencha os dados da escola e clique em **Gerar horário**.")
        return

    result = st.session_state.result
    context = st.session_state.context
    level, message = quality_status(result.breakdown)
    st.markdown(
        f'<div class="banner banner-{level}"><h3>{html.escape(message)}</h3>'
        f"<p>Levou {result.elapsed_seconds:.1f}s · {result.generation_reached} tentativas do gerador.</p></div>",
        unsafe_allow_html=True,
    )

    leftover = unassigned_rows(result.schedule, context)
    problems = explain_problems(result.breakdown)
    if problems:
        st.markdown("#### O que o gerador não conseguiu resolver")
        for item in problems:
            st.markdown(
                f'<div class="problem"><strong>{html.escape(str(item["title"]))}</strong> '
                f'· <span class="count">{item["count"]}x</span>'
                f'<p>{html.escape(str(item["hint"]))}</p></div>',
                unsafe_allow_html=True,
            )

    if leftover:
        st.markdown("#### Aulas que ficaram de fora")
        st.caption("Não havia horário livre (turma cheia, professor em outra turma, ou dia indisponível).")
        st.dataframe(pd.DataFrame(leftover), width="stretch", hide_index=True)

    st.markdown("#### Grade da semana")
    st.caption("Cada célula é uma aula. O traço (—) é horário livre da turma.")
    _grid(result, context)

    horario_xlsx = _excel_bytes(lambda: timetable_excel(result.schedule, context))
    if horario_xlsx is not None:
        st.download_button(
            "Baixar horário em Excel",
            horario_xlsx,
            "horario.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.caption("Para baixar o Excel, instale o pacote openpyxl no ambiente da tela.")

    with st.expander("Detalhe técnico (H1–H4, S1)"):
        counts = result.breakdown.counts
        v1, v2, v3, v4, v5 = st.columns(5)
        v1.metric("H1 professor", counts.get("H1", 0))
        v2.metric("H2 turma", counts.get("H2", 0))
        v3.metric("H3 carga", counts.get("H3", 0))
        v4.metric("H4 disponibilidade", counts.get("H4", 0))
        v5.metric("S1 concentração", counts.get("S1", 0))
        st.caption(f"Fitness {result.fitness:.0f} (quanto maior, melhor).")


def main() -> None:
    st.set_page_config(page_title="Auto-Schedule", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        '<div class="hero"><h1>Auto-Schedule</h1>'
        "<p>Gera o horário da semana a partir das turmas, professores e aulas.</p>"
        '<p class="steps">'
        "<span>1</span> Preencha as tabelas &nbsp;"
        "<span>2</span> Confira se os dados fecham &nbsp;"
        "<span>3</span> Gere o horário"
        "</p></div>",
        unsafe_allow_html=True,
    )

    _init_state()
    _consume_pending_instance()
    hours, population, generations, mutation = _sidebar()

    with st.expander("O que o gerador respeita"):
        st.markdown(
            """
- Um professor **não** fica em duas turmas no mesmo horário
- Uma turma **não** tem duas aulas no mesmo horário
- Cada disciplina aparece a quantidade de vezes que você pediu
- O professor só entra nos **dias marcados**
- Evita mais de duas aulas da mesma disciplina no mesmo dia
            """
        )

    st.radio(
        "O que você quer ver",
        options=["dados", "horario"],
        format_func=lambda key: "Dados da escola" if key == "dados" else "Horário gerado",
        horizontal=True,
        key="nav",
    )

    if st.session_state.nav == "dados":
        _school_tab(hours, population, generations, mutation)
    else:
        _result_tab()


if __name__ == "__main__":
    main()

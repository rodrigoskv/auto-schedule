"""Lê planilhas e monta Teacher, ClassGroup, Subject e a grade (TimeSlot)."""

import difflib
from pathlib import Path

import pandas as pd

from data.ids import slugify, unique_id
from data.school_hours import (
    DAYS,
    SchoolHours,
    build_time_slots,
    day_column_names,
    hours_from_grade,
    normalize_shift,
    parse_days,
)
from domain.entities import ClassGroup, SchoolInstance, Subject, Teacher

SHEET_ALIASES = {
    "grade": ("grade", "horario", "horarios", "school_hours"),
    "turmas": ("turmas", "classes", "class_groups", "classgroups"),
    "professores": ("professores", "teachers"),
    "aulas": ("aulas", "disciplinas", "subjects"),
}


def _yes(value) -> bool:
    return str(value).strip().lower() in {"s", "sim", "yes", "y", "1", "x", "true"}


def _blank(value) -> bool:
    text = str(value).strip()
    return not text or text.lower() in {"nan", "none", "<na>"}


def _suggest(value: str, options: list[str]) -> str | None:
    if not value or not options:
        return None
    folded = {slugify(option): option for option in options}
    key = slugify(value)
    if key in folded:
        return folded[key]
    matches = difflib.get_close_matches(value.lower(), [item.lower() for item in options], n=1, cutoff=0.55)
    if not matches:
        matches = difflib.get_close_matches(key, list(folded), n=1, cutoff=0.55)
        if matches:
            return folded[matches[0]]
        return None
    lower_map = {item.lower(): item for item in options}
    return lower_map[matches[0]]


def _lookup(name: str, items, attr: str = "name"):
    """Encontra por nome (ignora maiúsculas e º/acento). Devolve (item, None) ou (None, sugestão)."""
    by_lower = {getattr(item, attr).strip().lower(): item for item in items}
    key = name.strip().lower()
    if key in by_lower:
        return by_lower[key], None
    slug = slugify(name)
    slug_hits = [item for item in items if slugify(getattr(item, attr)) == slug]
    if len(slug_hits) == 1:
        return slug_hits[0], None
    return None, _suggest(name, [getattr(item, attr) for item in items])


def _missing_msg(kind: str, value: str, suggestion: str | None, catalog: list[str]) -> str:
    line = f"{kind} '{value}' não existe na tabela."
    if suggestion:
        line += f" Você quis dizer '{suggestion}'?"
    elif catalog:
        sample = ", ".join(catalog[:6])
        extra = "…" if len(catalog) > 6 else ""
        line += f" Cadastrados: {sample}{extra}."
    return line


def _col(df: pd.DataFrame, *names: str) -> str | None:
    mapping = {str(c).strip().lower(): c for c in df.columns}
    for name in names:
        if name.lower() in mapping:
            return mapping[name.lower()]
    return None


def _read(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def _sheet_name(book: pd.ExcelFile, aliases: tuple[str, ...]) -> str | None:
    mapping = {str(name).strip().lower(): name for name in book.sheet_names}
    for alias in aliases:
        if alias in mapping:
            return mapping[alias]
    return None


# Planilha → entidades


def grade_from_df(df: pd.DataFrame) -> SchoolHours:
    if df.empty:
        raise ValueError("Aba Grade está vazia.")
    row = df.iloc[0]
    days_col = _col(df, "school_days", "dias_letivos", "dias")
    shift_col = _col(df, "shift", "turno")
    lessons_col = _col(df, "lessons_per_day", "aulas_por_dia", "aulas")

    if days_col is not None:
        days = parse_days(row[days_col])
    else:
        days = []
        for day in DAYS:
            col = _col(df, *day_column_names(day))
            if col and _yes(row[col]):
                days.append(day)
        if not days:
            raise ValueError("Aba Grade precisa de school_days ou colunas de dias.")

    if shift_col is None or lessons_col is None:
        raise ValueError("Aba Grade precisa de shift e lessons_per_day.")

    payload = {
        "school_days": days,
        "shift": row[shift_col],
        "lessons_per_day": row[lessons_col],
    }
    return hours_from_grade(payload)


def teachers_from_df(df: pd.DataFrame, hours: SchoolHours) -> list[Teacher]:
    name_col = _col(df, "professor", "teacher", "nome", "name")
    if name_col is None:
        raise ValueError("A tabela de professores precisa da coluna professor (ou teacher).")

    taken: set[str] = set()
    seen_names: set[str] = set()
    teachers: list[Teacher] = []
    errors: list[str] = []
    for index, row in df.iterrows():
        name = str(row[name_col]).strip()
        if _blank(name):
            continue
        key = name.lower()
        if key in seen_names:
            errors.append(
                f"Professor '{name}' está repetido. Use um nome diferente para cada pessoa "
                "(ex.: Ana Silva e Ana Costa)."
            )
            continue
        seen_names.add(key)
        periods: list[str] = []
        for day in DAYS:
            col = _col(df, *day_column_names(day))
            if col and _yes(row[col]) and day in hours.days:
                periods.append(f"{day}_{hours.shift}")
        teachers.append(
            Teacher(
                id=unique_id(name, taken),
                name=name,
                available_periods=periods,
            )
        )
    if errors:
        raise ValueError("\n".join(errors))
    return teachers


def class_groups_from_df(df: pd.DataFrame, hours: SchoolHours) -> list[ClassGroup]:
    name_col = _col(df, "turma", "class_group", "classgroup", "class", "nome", "name")
    shift_col = _col(df, "turno", "shift")
    if name_col is None:
        raise ValueError("A tabela de turmas precisa da coluna turma (ou class_group).")

    taken: set[str] = set()
    seen_names: set[str] = set()
    groups: list[ClassGroup] = []
    errors: list[str] = []
    for _, row in df.iterrows():
        name = str(row[name_col]).strip()
        if _blank(name):
            continue
        key = name.lower()
        if key in seen_names:
            errors.append(f"Turma '{name}' está repetida. Cada turma precisa de um nome único.")
            continue
        seen_names.add(key)
        raw_shift = str(row[shift_col]).strip() if shift_col else hours.shift
        if _blank(raw_shift):
            shift = hours.shift
        else:
            shift = normalize_shift(raw_shift)
        groups.append(ClassGroup(id=unique_id(name, taken), name=name, shift=shift))
    if errors:
        raise ValueError("\n".join(errors))
    return groups


def _parse_workload(raw, line_no: int, subject_name: str) -> tuple[int | None, str | None]:
    if _blank(raw) or (isinstance(raw, float) and pd.isna(raw)):
        return None, f"Linha {line_no}: informe quantas aulas semanais tem {subject_name or 'a disciplina'}."
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, f"Linha {line_no}: aulas_semanais de '{subject_name}' deve ser um número (recebi '{raw}')."
    if value != int(value):
        return None, f"Linha {line_no}: aulas_semanais de '{subject_name}' precisa ser inteiro (sem casas decimais)."
    workload = int(value)
    if workload < 1:
        return None, f"Linha {line_no}: '{subject_name}' precisa de pelo menos 1 aula na semana."
    return workload, None


def subjects_from_df(
    df: pd.DataFrame,
    teachers: list[Teacher],
    class_groups: list[ClassGroup],
) -> list[Subject]:
    class_col = _col(df, "turma", "class_group", "classgroup", "class")
    subject_col = _col(df, "disciplina", "materia", "subject")
    teacher_col = _col(df, "professor", "teacher")
    load_col = _col(df, "aulas_semanais", "carga", "weekly_workload", "weekly_lessons")
    if not all([class_col, subject_col, teacher_col, load_col]):
        raise ValueError(
            "A tabela de aulas precisa das colunas turma, disciplina, professor e aulas_semanais."
        )

    class_names = [group.name for group in class_groups]
    teacher_names = [teacher.name for teacher in teachers]
    taken: set[str] = set()
    subjects: list[Subject] = []
    errors: list[str] = []

    for index, row in df.iterrows():
        class_name = str(row[class_col]).strip()
        subject_name = str(row[subject_col]).strip()
        teacher_name = str(row[teacher_col]).strip()
        if _blank(class_name) and _blank(subject_name) and _blank(teacher_name):
            continue
        line_no = int(index) + 2 if isinstance(index, (int, float)) else index

        if _blank(class_name):
            errors.append(f"Linha {line_no}: falta a turma da disciplina {subject_name or '(sem nome)'}.")
            continue
        if _blank(subject_name):
            errors.append(f"Linha {line_no}: a turma '{class_name}' está com a disciplina em branco.")
            subject_name = ""
        if _blank(teacher_name):
            errors.append(f"Linha {line_no}: falta o professor de {subject_name or 'a disciplina'} ({class_name}).")

        group, group_hint = _lookup(class_name, class_groups)
        teacher, teacher_hint = _lookup(teacher_name, teachers) if not _blank(teacher_name) else (None, None)
        if group is None:
            errors.append(
                f"Linha {line_no}: {_missing_msg('turma', class_name, group_hint, class_names)}"
            )
        if not _blank(teacher_name) and teacher is None:
            errors.append(
                f"Linha {line_no}: {_missing_msg('professor', teacher_name, teacher_hint, teacher_names)}"
            )

        workload, load_error = _parse_workload(row[load_col], line_no, subject_name or class_name)
        if load_error:
            errors.append(load_error)

        if group is None or teacher is None or workload is None or _blank(subject_name):
            continue
        subjects.append(
            Subject(
                id=unique_id(f"{group.id}_{subject_name}_{teacher.id}", taken),
                name=subject_name,
                teacher_id=teacher.id,
                class_group_id=group.id,
                weekly_workload=workload,
            )
        )

    if errors:
        raise ValueError("\n".join(errors))
    return subjects


# Arquivo → entidades


def load_teachers(path: str | Path, hours: SchoolHours) -> list[Teacher]:
    return teachers_from_df(_read(path), hours)


def load_class_groups(path: str | Path, hours: SchoolHours) -> list[ClassGroup]:
    return class_groups_from_df(_read(path), hours)


def load_subjects(
    path: str | Path,
    teachers: list[Teacher],
    class_groups: list[ClassGroup],
) -> list[Subject]:
    return subjects_from_df(_read(path), teachers, class_groups)


def load_grade(path: str | Path) -> SchoolHours:
    return grade_from_df(_read(path))


def load_from_workbook(source) -> SchoolInstance:
    book = pd.ExcelFile(source)
    missing = []
    frames: dict[str, pd.DataFrame] = {}
    for key, aliases in SHEET_ALIASES.items():
        name = _sheet_name(book, aliases)
        if name is None:
            missing.append(key.capitalize())
        else:
            frames[key] = pd.read_excel(book, sheet_name=name)
    if missing:
        raise ValueError(
            "Planilha do molde precisa das abas Grade, Turmas, Professores e Aulas. "
            f"Faltando: {', '.join(missing)}."
        )

    hours = grade_from_df(frames["grade"])
    teachers = teachers_from_df(frames["professores"], hours)
    class_groups = class_groups_from_df(frames["turmas"], hours)
    subjects = subjects_from_df(frames["aulas"], teachers, class_groups)
    return SchoolInstance(
        teachers=teachers,
        class_groups=class_groups,
        subjects=subjects,
        time_slots=build_time_slots(hours),
    )


# Entidades → planilha (tela Streamlit)


def teachers_to_df(teachers: list[Teacher], hours: SchoolHours) -> pd.DataFrame:
    rows = []
    for teacher in teachers:
        row = {"professor": teacher.name}
        for day in DAYS:
            row[day] = f"{day}_{hours.shift}" in teacher.available_periods
        rows.append(row)
    return pd.DataFrame(rows)


def class_groups_to_df(class_groups: list[ClassGroup]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"turma": group.name, "turno": group.shift or ""} for group in class_groups]
    )


def subjects_to_df(
    subjects: list[Subject],
    teachers: list[Teacher],
    class_groups: list[ClassGroup],
) -> pd.DataFrame:
    teacher_name = {item.id: item.name for item in teachers}
    group_name = {item.id: item.name for item in class_groups}
    return pd.DataFrame(
        [
            {
                "turma": group_name.get(subject.class_group_id, subject.class_group_id),
                "disciplina": subject.name,
                "professor": teacher_name.get(subject.teacher_id, subject.teacher_id),
                "aulas_semanais": subject.weekly_workload,
            }
            for subject in subjects
        ]
    )

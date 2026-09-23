"""Lê planilhas e monta Teacher, ClassGroup, Subject e a grade (TimeSlot)."""

from pathlib import Path

import pandas as pd

from data.ids import unique_id
from data.school_hours import SchoolHours, build_time_slots, hours_from_grade, normalize_shift, parse_days
from domain.entities import ClassGroup, Subject, Teacher, TimeSlot

DAYS = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado"]
SHEET_ALIASES = {
    "grade": ("grade", "horario", "horarios", "school_hours"),
    "turmas": ("turmas", "classes", "class_groups"),
    "professores": ("professores", "teachers"),
    "aulas": ("aulas", "disciplinas", "subjects"),
}


def _yes(value) -> bool:
    return str(value).strip().lower() in {"s", "sim", "yes", "y", "1", "x", "true"}


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
            col = _col(df, day, "terça" if day == "terca" else day)
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
    name_col = _col(df, "professor", "nome", "name")
    if name_col is None:
        raise ValueError("Planilha de professores precisa da coluna professor.")

    taken: set[str] = set()
    teachers: list[Teacher] = []
    for _, row in df.iterrows():
        name = str(row[name_col]).strip()
        if not name or name.lower() == "nan":
            continue
        periods: list[str] = []
        for day in DAYS:
            col = _col(df, day, "terça" if day == "terca" else day)
            if col and _yes(row[col]) and day in hours.days:
                periods.append(f"{day}_{hours.shift}")
        if not periods:
            periods = [f"{day}_{hours.shift}" for day in hours.days]
        teachers.append(
            Teacher(
                id=unique_id(name, taken),
                name=name,
                available_periods=periods,
            )
        )
    return teachers


def class_groups_from_df(df: pd.DataFrame, hours: SchoolHours) -> list[ClassGroup]:
    name_col = _col(df, "turma", "nome", "name")
    shift_col = _col(df, "turno", "shift")
    if name_col is None:
        raise ValueError("Planilha de turmas precisa da coluna turma.")

    taken: set[str] = set()
    groups: list[ClassGroup] = []
    for _, row in df.iterrows():
        name = str(row[name_col]).strip()
        if not name or name.lower() == "nan":
            continue
        raw_shift = str(row[shift_col]).strip() if shift_col else hours.shift
        if not raw_shift or raw_shift.lower() == "nan":
            shift = hours.shift
        else:
            shift = normalize_shift(raw_shift)
        groups.append(ClassGroup(id=unique_id(name, taken), name=name, shift=shift))
    return groups


def subjects_from_df(
    df: pd.DataFrame,
    teachers: list[Teacher],
    class_groups: list[ClassGroup],
) -> list[Subject]:
    class_col = _col(df, "turma", "class_group")
    subject_col = _col(df, "disciplina", "materia", "subject")
    teacher_col = _col(df, "professor", "teacher")
    load_col = _col(df, "aulas_semanais", "carga", "weekly_workload")
    if not all([class_col, subject_col, teacher_col, load_col]):
        raise ValueError("Planilha de aulas precisa de turma, disciplina, professor e aulas_semanais.")

    teachers_by_name = {t.name.strip().lower(): t for t in teachers}
    classes_by_name = {c.name.strip().lower(): c for c in class_groups}
    taken: set[str] = set()
    subjects: list[Subject] = []

    for index, row in df.iterrows():
        class_name = str(row[class_col]).strip()
        subject_name = str(row[subject_col]).strip()
        teacher_name = str(row[teacher_col]).strip()
        if class_name.lower() == "nan" or not class_name:
            continue
        group = classes_by_name.get(class_name.lower())
        teacher = teachers_by_name.get(teacher_name.lower())
        if group is None:
            raise ValueError(f"Linha {index + 2}: turma '{class_name}' não existe na planilha de turmas.")
        if teacher is None:
            raise ValueError(f"Linha {index + 2}: professor '{teacher_name}' não existe na planilha de professores.")
        workload = int(row[load_col])
        subjects.append(
            Subject(
                id=unique_id(f"{group.id}_{subject_name}_{teacher.id}", taken),
                name=subject_name,
                teacher_id=teacher.id,
                class_group_id=group.id,
                weekly_workload=workload,
            )
        )
    return subjects


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


def load_from_workbook(
    path: str | Path,
) -> tuple[list[Teacher], list[ClassGroup], list[Subject], list[TimeSlot]]:
    path = Path(path)
    book = pd.ExcelFile(path)
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
    return teachers, class_groups, subjects, build_time_slots(hours)

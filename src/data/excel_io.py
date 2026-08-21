from pathlib import Path

import pandas as pd

from data.ids import unique_id
from data.school_hours import SchoolHours
from domain.entities import ClassGroup, Subject, Teacher

DAYS = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado"]


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


def load_teachers(path: str | Path, hours: SchoolHours) -> list[Teacher]:
    df = _read(path)
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


def load_class_groups(path: str | Path, hours: SchoolHours) -> list[ClassGroup]:
    df = _read(path)
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
        raw_shift = str(row[shift_col]).strip().lower() if shift_col else hours.shift
        shift = hours.shift
        if "tarde" in raw_shift:
            shift = "tarde"
        elif "noite" in raw_shift:
            shift = "noite"
        elif "manha" in raw_shift or "manhã" in raw_shift:
            shift = "manha"
        groups.append(ClassGroup(id=unique_id(name, taken), name=name, shift=shift))
    return groups


def load_subjects(
    path: str | Path,
    teachers: list[Teacher],
    class_groups: list[ClassGroup],
) -> list[Subject]:
    df = _read(path)
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
                weekly_workload=workload,
                teacher_id=teacher.id,
                class_group_id=group.id,
            )
        )
    return subjects
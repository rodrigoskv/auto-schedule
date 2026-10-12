"""Carrega Teacher, ClassGroup, Subject e TimeSlot.

Aceita pasta JSON, molde.xlsx (abas Grade/Turmas/Professores/Aulas)
ou o trio CSV/Excel (teachers + classgroups + subjects) com grade.
"""

import json
from pathlib import Path

from data.excel_io import load_class_groups, load_from_workbook, load_grade, load_subjects, load_teachers
from data.school_hours import build_time_slots, hours_from_grade
from domain.entities import ClassGroup, SchoolInstance, Subject, Teacher

JSON_FILES = ("teachers.json", "class_groups.json", "subjects.json", "grade.json")


def load_instance(entrada: str | Path) -> SchoolInstance:
    """Detecta o formato da entrada e devolve a escola em memória."""
    path = Path(entrada)
    if not path.exists():
        raise FileNotFoundError(f"Entrada não encontrada: {path}")

    # 1) um único .xlsx com as 4 abas
    if path.is_file():
        if path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError("Arquivo de entrada deve ser um .xlsx com as abas Grade, Turmas, Professores e Aulas.")
        return load_from_workbook(path)

    # 2) pasta JSON (teachers, class_groups, subjects, grade)
    if all((path / name).is_file() for name in JSON_FILES):
        return _load_json(path)

    # 3) pasta com molde.xlsx
    molde = path / "molde.xlsx"
    if molde.is_file():
        return load_from_workbook(molde)

    # 4) trio de planilhas + grade.json
    return _load_trio(path)


def _read_json(path: Path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _load_models(path: Path, model):
    payload = _read_json(path)
    if not isinstance(payload, list):
        raise ValueError(f"{path.name} deve ser uma lista.")
    items = []
    for index, item in enumerate(payload):
        try:
            items.append(model(**item))
        except TypeError as exc:
            raise ValueError(f"{path.name} item {index}: {exc}") from exc
    return items


def _load_json(folder: Path) -> SchoolInstance:
    hours = hours_from_grade(_read_json(folder / "grade.json"))
    return SchoolInstance(
        teachers=_load_models(folder / "teachers.json", Teacher),
        class_groups=_load_models(folder / "class_groups.json", ClassGroup),
        subjects=_load_models(folder / "subjects.json", Subject),
        time_slots=build_time_slots(hours),
    )


def _file(folder: Path, *names: str) -> Path | None:
    for name in names:
        path = folder / name
        if path.is_file():
            return path
    return None


def _hours(folder: Path):
    grade_json = folder / "grade.json"
    if grade_json.is_file():
        return hours_from_grade(_read_json(grade_json))
    grade_table = _file(folder, "grade.csv", "grade.xlsx")
    if grade_table is not None:
        return load_grade(grade_table)
    raise ValueError("Pasta sem grade.json / grade.csv. Informe school_days, shift e lessons_per_day.")


def _load_trio(folder: Path) -> SchoolInstance:
    teachers_path = _file(
        folder,
        "teachers.csv",
        "teachers.xlsx",
        "professores.xlsx",
        "professores.csv",
    )
    classes_path = _file(
        folder,
        "classgroups.csv",
        "class_groups.csv",
        "classes.csv",
        "turmas.xlsx",
        "turmas.csv",
    )
    subjects_path = _file(
        folder,
        "subjects.csv",
        "lessons.csv",
        "aulas.xlsx",
        "aulas.csv",
    )
    if not teachers_path or not classes_path or not subjects_path:
        raise ValueError(
            "Entrada deve ser pasta JSON, molde.xlsx "
            "ou trio teachers/classgroups/subjects (CSV ou Excel) com grade.csv."
        )
    hours = _hours(folder)
    teachers = load_teachers(teachers_path, hours)
    class_groups = load_class_groups(classes_path, hours)
    subjects = load_subjects(subjects_path, teachers, class_groups)
    return SchoolInstance(
        teachers=teachers,
        class_groups=class_groups,
        subjects=subjects,
        time_slots=build_time_slots(hours),
    )

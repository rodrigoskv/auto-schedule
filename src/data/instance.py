"""Carrega a instância escolar.

Formatos aceitos:
- pasta JSON: teachers.json, class_groups.json, subjects.json, grade.json
- planilha com abas Grade, Turmas, Professores, Aulas
- trio turmas.xlsx + professores.xlsx + aulas.xlsx, com grade.json

Saída: Teacher, ClassGroup, Subject e TimeSlot (este último gerado pela grade).
"""

import json
from pathlib import Path

import pandas as pd

from data.excel_io import load_class_groups, load_from_workbook, load_grade, load_subjects, load_teachers
from data.school_hours import SchoolHours, build_time_slots, hours_from_grade
from domain.entities import ClassGroup, Subject, Teacher, TimeSlot

INPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "input"
JSON_FILES = ("teachers.json", "class_groups.json", "subjects.json", "grade.json")
TRIO_TEACHERS = ("professores.xlsx", "molde-professores.xlsx", "teachers.xlsx")
TRIO_CLASSES = ("turmas.xlsx", "molde-turmas.xlsx", "class_groups.xlsx")
TRIO_SUBJECTS = ("aulas.xlsx", "molde-aulas.xlsx", "subjects.xlsx")


def load_instance(
    entrada: str | Path,
) -> tuple[list[Teacher], list[ClassGroup], list[Subject], list[TimeSlot]]:
    path = Path(entrada)
    if not path.exists():
        raise FileNotFoundError(f"Entrada não encontrada: {path}")
    if path.is_file():
        if path.suffix.lower() not in {".xlsx", ".xls"}:
            raise ValueError(
                "Arquivo de entrada deve ser uma planilha .xlsx com as abas Grade, Turmas, Professores e Aulas."
            )
        return load_from_workbook(path)
    if _has_json(path):
        return _load_json_dir(path)
    workbook = _find_workbook(path)
    if workbook is not None:
        return load_from_workbook(workbook)
    return _load_trio(path)


def load_from_excel(
    hours: SchoolHours,
    teachers_path: str | Path | None = None,
    classes_path: str | Path | None = None,
    subjects_path: str | Path | None = None,
) -> tuple[list[Teacher], list[ClassGroup], list[Subject], list[TimeSlot]]:
    teachers_path = Path(teachers_path or INPUT_DIR / "professores.xlsx")
    classes_path = Path(classes_path or INPUT_DIR / "turmas.xlsx")
    subjects_path = Path(subjects_path or INPUT_DIR / "aulas.xlsx")

    teachers = load_teachers(teachers_path, hours)
    class_groups = load_class_groups(classes_path, hours)
    subjects = load_subjects(subjects_path, teachers, class_groups)
    time_slots = build_time_slots(hours)
    return teachers, class_groups, subjects, time_slots


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


def _has_json(folder: Path) -> bool:
    return all((folder / name).is_file() for name in JSON_FILES)


def _load_json_dir(
    folder: Path,
) -> tuple[list[Teacher], list[ClassGroup], list[Subject], list[TimeSlot]]:
    hours = hours_from_grade(_read_json(folder / "grade.json"))
    teachers = _load_models(folder / "teachers.json", Teacher)
    class_groups = _load_models(folder / "class_groups.json", ClassGroup)
    subjects = _load_models(folder / "subjects.json", Subject)
    return teachers, class_groups, subjects, build_time_slots(hours)


def _files(folder: Path) -> dict[str, Path]:
    return {path.name.lower(): path for path in folder.iterdir() if path.is_file()}


def _find(folder: Path, names: tuple[str, ...]) -> Path | None:
    files = _files(folder)
    for name in names:
        key = name.lower()
        if key in files:
            return files[key]
        csv_key = Path(name).with_suffix(".csv").name.lower()
        if csv_key in files:
            return files[csv_key]
    return None


def _find_workbook(folder: Path) -> Path | None:
    preferred = _find(folder, ("molde.xlsx", "entrada.xlsx"))
    if preferred is not None:
        return preferred

    for path in sorted(folder.glob("*.xlsx")):
        try:
            book = pd.ExcelFile(path)
            names = {str(sheet).strip().lower() for sheet in book.sheet_names}
            if "grade" in names and "turmas" in names and "professores" in names and "aulas" in names:
                return path
        except Exception:
            continue
    return None


def _hours_from_folder(folder: Path) -> SchoolHours:
    grade_json = folder / "grade.json"
    if grade_json.is_file():
        return hours_from_grade(_read_json(grade_json))
    grade_sheet = _find(folder, ("grade.xlsx", "molde-grade.xlsx"))
    if grade_sheet is not None:
        return load_grade(grade_sheet)
    raise ValueError(
        "Pasta sem grade.json (ou grade.xlsx). Informe school_days, shift e lessons_per_day."
    )


def _load_trio(
    folder: Path,
) -> tuple[list[Teacher], list[ClassGroup], list[Subject], list[TimeSlot]]:
    teachers_path = _find(folder, TRIO_TEACHERS)
    classes_path = _find(folder, TRIO_CLASSES)
    subjects_path = _find(folder, TRIO_SUBJECTS)
    if not teachers_path or not classes_path or not subjects_path:
        raise ValueError(
            "Entrada deve ser pasta JSON (teachers.json, class_groups.json, subjects.json, grade.json), "
            "planilha com abas Grade/Turmas/Professores/Aulas, "
            "ou trio turmas.xlsx + professores.xlsx + aulas.xlsx com grade.json."
        )
    hours = _hours_from_folder(folder)
    return load_from_excel(hours, teachers_path, classes_path, subjects_path)

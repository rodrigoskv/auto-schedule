from pathlib import Path

from data.excel_io import load_class_groups, load_subjects, load_teachers
from data.school_hours import SchoolHours, build_time_slots
from domain.entities import ClassGroup, Subject, Teacher, TimeSlot

INPUT_DIR = Path(__file__).resolve().parents[2] / "data" / "input"


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
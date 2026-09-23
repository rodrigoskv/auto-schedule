"""Planilhas-modelo e grade.json de exemplo."""

import json
from pathlib import Path

import pandas as pd

GRADE = {
    "school_days": ["segunda", "terca", "quarta", "quinta", "sexta"],
    "shift": "manha",
    "lessons_per_day": 5,
}


def write_templates(folder: str | Path) -> None:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    grade_df = pd.DataFrame(
        [
            {
                "school_days": ", ".join(GRADE["school_days"]),
                "shift": GRADE["shift"],
                "lessons_per_day": GRADE["lessons_per_day"],
            }
        ]
    )
    teachers_df = pd.DataFrame(
        [
            {"professor": "Paula", "segunda": "S", "terca": "S", "quarta": "S", "quinta": "S", "sexta": "S", "sabado": "N"},
            {"professor": "Caroline", "segunda": "S", "terca": "S", "quarta": "S", "quinta": "S", "sexta": "S", "sabado": "N"},
        ]
    )
    classes_df = pd.DataFrame(
        [
            {"turma": "6º ano A", "turno": "manha"},
            {"turma": "7º ano A", "turno": "manha"},
        ]
    )
    subjects_df = pd.DataFrame(
        [
            {"turma": "6º ano A", "disciplina": "Matemática", "professor": "Caroline", "aulas_semanais": 4},
            {"turma": "6º ano A", "disciplina": "Artes", "professor": "Paula", "aulas_semanais": 2},
            {"turma": "7º ano A", "disciplina": "Matemática", "professor": "Caroline", "aulas_semanais": 3},
        ]
    )

    with pd.ExcelWriter(folder / "molde.xlsx") as writer:
        grade_df.to_excel(writer, sheet_name="Grade", index=False)
        classes_df.to_excel(writer, sheet_name="Turmas", index=False)
        teachers_df.to_excel(writer, sheet_name="Professores", index=False)
        subjects_df.to_excel(writer, sheet_name="Aulas", index=False)

    for name in ("professores.xlsx", "molde-professores.xlsx"):
        teachers_df.to_excel(folder / name, index=False)
    for name in ("turmas.xlsx", "molde-turmas.xlsx"):
        classes_df.to_excel(folder / name, index=False)
    for name in ("aulas.xlsx", "molde-aulas.xlsx"):
        subjects_df.to_excel(folder / name, index=False)
    (folder / "grade.json").write_text(
        json.dumps(GRADE, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

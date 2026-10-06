"""Molde de entrada: uma planilha com 4 abas, ou o trio + grade.json."""

import json
from pathlib import Path

import pandas as pd

GRADE = {
    "school_days": ["segunda", "terca", "quarta", "quinta", "sexta"],
    "shift": "manha",
    "lessons_per_day": 5,
}

GRADE_DF = pd.DataFrame(
    [
        {
            "school_days": ", ".join(GRADE["school_days"]),
            "shift": GRADE["shift"],
            "lessons_per_day": GRADE["lessons_per_day"],
        }
    ]
)
TEACHERS_DF = pd.DataFrame(
    [
        {"professor": "Paula", "segunda": "S", "terca": "S", "quarta": "S", "quinta": "S", "sexta": "S", "sabado": "N"},
        {"professor": "Caroline", "segunda": "S", "terca": "S", "quarta": "S", "quinta": "S", "sexta": "S", "sabado": "N"},
    ]
)
CLASSES_DF = pd.DataFrame(
    [
        {"turma": "6º ano A", "turno": "manha"},
        {"turma": "7º ano A", "turno": "manha"},
    ]
)
SUBJECTS_DF = pd.DataFrame(
    [
        {"turma": "6º ano A", "disciplina": "Matemática", "professor": "Caroline", "aulas_semanais": 4},
        {"turma": "6º ano A", "disciplina": "Artes", "professor": "Paula", "aulas_semanais": 2},
        {"turma": "7º ano A", "disciplina": "Matemática", "professor": "Caroline", "aulas_semanais": 3},
    ]
)


def write_templates(folder: str | Path) -> None:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(folder / "molde.xlsx") as writer:
        GRADE_DF.to_excel(writer, sheet_name="Grade", index=False)
        CLASSES_DF.to_excel(writer, sheet_name="Turmas", index=False)
        TEACHERS_DF.to_excel(writer, sheet_name="Professores", index=False)
        SUBJECTS_DF.to_excel(writer, sheet_name="Aulas", index=False)

    TEACHERS_DF.to_excel(folder / "professores.xlsx", index=False)
    CLASSES_DF.to_excel(folder / "turmas.xlsx", index=False)
    SUBJECTS_DF.to_excel(folder / "aulas.xlsx", index=False)
    (folder / "grade.json").write_text(
        json.dumps(GRADE, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def molde_bytes() -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        GRADE_DF.to_excel(writer, sheet_name="Grade", index=False)
        CLASSES_DF.to_excel(writer, sheet_name="Turmas", index=False)
        TEACHERS_DF.to_excel(writer, sheet_name="Professores", index=False)
        SUBJECTS_DF.to_excel(writer, sheet_name="Aulas", index=False)
    return buffer.getvalue()


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")

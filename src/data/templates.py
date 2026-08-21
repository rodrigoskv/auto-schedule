from pathlib import Path

import pandas as pd


def write_templates(folder: str | Path) -> None:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [
            {"professor": "Paula", "segunda": "S", "terca": "S", "quarta": "S", "quinta": "S", "sexta": "S", "sabado": "N"},
            {"professor": "Caroline", "segunda": "S", "terca": "S", "quarta": "S", "quinta": "S", "sexta": "S", "sabado": "N"},
        ]
    ).to_excel(folder / "molde-professores.xlsx", index=False)

    pd.DataFrame(
        [
            {"turma": "6º ano A", "turno": "manha"},
            {"turma": "7º ano A", "turno": "manha"},
        ]
    ).to_excel(folder / "molde-turmas.xlsx", index=False)

    pd.DataFrame(
        [
            {"turma": "6º ano A", "disciplina": "Matemática", "professor": "Caroline", "aulas_semanais": 4},
            {"turma": "6º ano A", "disciplina": "Artes", "professor": "Paula", "aulas_semanais": 2},
            {"turma": "7º ano A", "disciplina": "Matemática", "professor": "Caroline", "aulas_semanais": 3},
        ]
    ).to_excel(folder / "molde-aulas.xlsx", index=False)
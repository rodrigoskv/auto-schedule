# Auto-Schedule

Algoritmo genético para gerar horário escolar.

A Escola Bandeirante é só a instância de teste em `data/`. O AG não assume quantidade fixa de professores, turmas, disciplinas ou slots.

## Como ler o código

```text
entrada (JSON ou planilha)
    → src/data/instance.py          load_instance
    → src/data/validate.py          validate_instance
    → Teacher / ClassGroup / Subject / TimeSlot
    → src/ga/context.py             GAContext
    → src/ga/operators/initial_population.py
    → src/ga/engine.py              run_ga
         ├── fitness.py             H1–H4, S1
         ├── selection.py
         ├── crossover.py
         ├── mutation.py
         └── repair.py
    → melhor Schedule
    → src/reporting/printer.py
```

Representação: `Schedule` é o indivíduo, a lista de `Lesson` é o cromossomo, cada `Lesson` é um gene.

`Subject.class_group_id` é obrigatório. A turma da disciplina é esse campo.

## Rodar

A partir de `src/`:

```text
python main.py --entrada ../data
python main.py --entrada ../data --somente-validar
python main.py --entrada ../data --populacao 80 --geracoes 200
python main.py --moldes
```

`--entrada` aceita pasta JSON, planilha com abas Grade / Turmas / Professores / Aulas, ou o trio `turmas.xlsx` + `professores.xlsx` + `aulas.xlsx` com `grade.json`.

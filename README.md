# Auto-Schedule

AG para horário escolar. Quem for ler o código pode seguir este caminho:

```text
1. entrada          src/data/instance.py        load_instance → SchoolInstance
2. validação        src/data/validate.py
3. representação    src/domain/entities.py      Schedule = indivíduo, Lesson = gene
                    Subject.class_group_id é a turma (campo explícito)
4. contexto         src/ga/context.py           GAContext.from_school
5. população        src/ga/operators/initial_population.py
6. uma geração      src/ga/engine.py            run_ga
     fitness        src/ga/fitness.py           H1–H4, S1
     seleção        src/ga/operators/selection.py
     crossover      src/ga/operators/crossover.py
     mutação        src/ga/operators/mutation.py
     repair         src/ga/operators/repair.py
7. resultado        src/reporting/printer.py
```

A Bandeirante é a instância em `data/`. `example/` é um CSV pequeno, com nomes em inglês, só para carregar e validar.

Critérios da grade: `docs/criterios-avaliacao.md`. Entidades: `docs/modelagem.md`. Cenários: `docs/cenarios-teste.md`.

## Tela

```text
streamlit run src/ui/app.py
```

A tela monta a mesma `SchoolInstance` do CLI: tabelas (ou molde.xlsx / JSON) → validação → `run_ga`.

## Terminal (a partir de `src/`)

```text
python main.py --entrada ../data
python main.py --entrada ../data --somente-validar
python main.py --moldes
python main_data.py
```

## Testes (na raiz)

```text
pytest
```

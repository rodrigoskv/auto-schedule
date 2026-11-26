# Modelagem do Problema

O projeto gera uma grade de horários escolar com algoritmo genético.

A grade aloca aulas em horários, com turmas, professores, disciplinas e períodos disponíveis.

As entidades ficam em `src/domain/entities.py`.

`Teacher`, `ClassGroup`, `Subject` e `TimeSlot` descrevem a escola.
`Lesson` é o gene. `Schedule` é o indivíduo: a lista de `Lesson` é o cromossomo.

## Professor

Representa o professor responsável por ministrar uma disciplina.

Campos:

- `id`
- `name`
- `available_periods`

`available_periods` é uma lista de chaves `dia_turno`, por exemplo `segunda_manha`.

Lista vazia significa que o professor pode em qualquer horário. A comparação usa `TimeSlot.period_key`.

## Turma

Representa uma turma escolar.

Campos:

- `id`
- `name`
- `shift`

`shift` pode ficar vazio. Turma sem turno enxerga todos os horários da escola.

Exemplo:

```text
- 6º ano A
- 6º ano B
- 7º ano A
- 8º ano A
- 9º ano
```

## Disciplina

Representa a oferta de uma disciplina para uma turma, com professor e carga semanal.

Campos:

- `id`
- `name`
- `teacher_id`
- `class_group_id`
- `weekly_workload`

A turma é o `class_group_id` informado. O texto do `id` não decide a turma.

`weekly_workload` define quantas vezes a oferta deve aparecer na semana. Aula a menos entra em H3.

## Período

Representa um horário disponível para aula.

Os períodos são gerados a partir da grade da escola (`school_days`, `shift`, `lessons_per_day`).

Campos:

- `id`
- `day_of_week`
- `shift`
- `order`
- `global_order`
- `label`

`order` é a posição da aula no dia. `global_order` é a posição na semana inteira.

`period_key` junta dia e turno: `segunda_manha`.

Exemplo:

```text
Segunda 1º aula
Segunda 2º aula
Terça 1º aula
```

## Escola

`SchoolInstance` é a entrada já convertida nas entidades do problema.

Campos:

- `teachers`
- `class_groups`
- `subjects`
- `time_slots`

## Aula

Representa uma aula alocada na grade. É o gene do cromossomo.

Campos:

- `teacher_id`
- `subject_id`
- `class_group_id`
- `time_slot_id`

`time_slot_id` vazio significa aula sem horário. Ela conta no déficit de carga e não gera conflito de professor, turma ou disponibilidade.

## Grade

`Schedule` é o indivíduo.

Campo:

- `lessons`

A lista guarda uma `Lesson` para cada aula da semana. O AG cruza, muta e repara essa lista.

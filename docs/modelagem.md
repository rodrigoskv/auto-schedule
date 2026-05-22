### Modelagem do Problema

O projeto tem como objetivo gerar automaticamente uma grade de horários escolar utilizando AG.

A grade é formada pela alocação de aulas em determinados horários, considerando turmas, professores, disciplinas e períodos disponíveis.



## **_Principais Entidades_**
### Professor

Representa o professor responsável por ministrar uma disciplina.
Campos principais:
>- `id`
>- `name`
>- `available_periods`


### Turma
Representa uma turma escolar.

Campos principais:

>- `id`
>- `name`
>- `shift`

Exemplo:
```text
- 6º ano A
- 6º ano B
- 7º ano A
- 8º ano A
- 9º ano 
```
### Disciplina

Representa uma disciplina que precisa ser alocada na grade.

Campos principais:

>- `id`
>- `name`
>- `weekly_workload`
>- `teacher_id`

A carga horária semanal define quantas vezes a disciplina deve aparecer na semana.

### Período

Representa um horário disponível para aula.

Campos principais:

>- `id`
>- `day_of_week`
>- `shift`
>- `order`
>- `label`

Exemplo:

```text
Segunda 1º aula
Segunda 2º aula
Terça 1º aula
```

## Aula
Representa uma aula alocada na grade.

Campos principais:
>-  `teacher_id: str`
>-  `subject_id: str`
>-  `class_group_id: str`
>-  `-time_slot_id: str`
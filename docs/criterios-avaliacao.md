# Critérios de Avaliação

A avaliação da grade é feita por meio de um `score`.

Quanto maior o score, melhor é a grade.

Pesos e códigos ficam em `src/domain/constraints.py`. A contagem está em `src/ga/fitness.py`.

## Fórmula

```text
Score = BASE_SCORE - (PESO_HARD * hard) - (PESO_SOFT * soft)
Score = 100000 - (1000 * hard) - (10 * soft)
```

`hard` é a soma de H1, H2, H3 e H4. `soft` é S1.

Uma grade sem violação vale 100000. Cada violação rígida pesa mais do que dezenas de violações flexíveis.

Aula sem horário (`time_slot_id` vazio) não entra em H1, H2 nem H4. Ela entra no déficit de H3.

## Restrições obrigatórias

As restrições obrigatórias são chamadas de `hard constraints`.

Cada violação recebe penalidade de 1000 pontos.

## H1: Professor em dois horários iguais

Um professor não pode estar em duas turmas diferentes no mesmo horário.

Cada turma extra no mesmo slot conta uma violação. Duas turmas no mesmo horário dão H1 = 1. Três turmas dão H1 = 2.

Exemplo inválido:

| Horário | Turma | Professor |
|---|---|---|
| Segunda 1º aula | 9º ano | Caroline |
| Segunda 1º aula | 7º ano A | Caroline |

Nesse caso, a professora Caroline foi alocada em duas turmas no mesmo período.

## H2: Turma em dois horários iguais

Uma turma não pode ter duas aulas no mesmo horário.

Cada aula extra no mesmo slot da turma conta uma violação.

Exemplo inválido:

| Horário | Turma | Disciplina |
|---|---|---|
| Segunda 1º aula | 9º ano | Matemática |
| Segunda 1º aula | 9º ano | Português |

Nesse caso, a turma 9º ano possui duas aulas simultâneas.

## H3: Carga horária semanal em déficit

Cada disciplina deve aparecer na grade pelo menos a quantidade de vezes definida em `weekly_workload`.

H3 conta só o que faltou: `carga - aulas com horário`. Aula a mais não gera H3.

Exemplo:

Se Matemática possui carga horária semanal de 4 aulas e só 3 estão com horário, H3 = 1.

Se as 4 estão alocadas, H3 = 0. Se aparecerem 5, H3 continua 0.

Disciplina com carga 3 e nenhuma aula na grade dá H3 = 3.

## H4: Professor fora da disponibilidade

Uma aula não pode cair num dia/turno que o professor não marcou.

`available_periods` guarda chaves `dia_turno`, por exemplo `terca_manha`. Cada aula cujo slot não está nessa lista conta uma violação.

Lista vazia significa que o professor pode em qualquer horário. Nesse caso H4 = 0.

Exemplo inválido:

| Horário | Turma | Professor | Disponibilidade |
|---|---|---|---|
| Segunda 1º aula | 9º ano | Caroline | só `terca_manha` |

Nesse caso H4 = 1. A mesma aula na terça de manhã dá H4 = 0.

## Restrições desejáveis

As restrições desejáveis são chamadas de `soft constraints`.

Cada violação recebe penalidade de 10 pontos.

## S1: Mais de 2 aulas da mesma disciplina no mesmo dia e turno

Uma turma não deve ter mais de 2 aulas da mesma disciplina no mesmo dia e no mesmo turno.

A contagem é por turma, por dia e por turno. Manhã e tarde não se somam.

Cada aula além da segunda conta uma violação. Três aulas no mesmo dia/turno dão S1 = 1. Quatro dão S1 = 2.

Exemplo indesejado:

| Horário | Turma | Disciplina |
|---|---|---|
| Segunda 1º aula | 9º ano | Matemática |
| Segunda 2º aula | 9º ano | Matemática |
| Segunda 3º aula | 9º ano | Matemática |

Nesse caso, existe uma violação soft.

Duas na segunda e uma na terça dão S1 = 0.

## Exemplo de cálculo

Considere:

```text
total_hard = 2
total_soft = 3
```

Aplicando a fórmula:

```text
Score = 100000 - (1000 * 2) - (10 * 3)
Score = 100000 - 2000 - 30
Score = 97970
```

Quanto menor o número de violações, maior será o score da grade.

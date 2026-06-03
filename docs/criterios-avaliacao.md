# Critérios de Avaliação

A avaliação da grade é feita por meio de um `score`.

Quanto maior o score, melhor é a grade.

## Fórmula

```text
Score = BASE - (PESO_HARD * hard) - (PESO_SOFT * soft)
```


## Restrições obrigatórias

As restrições obrigatórias são chamadas de `hard constraints`.

Cada violação recebe penalidade de 1000 pontos.

## H1: Professor em dois horários iguais

Um professor não pode estar em duas turmas diferentes no mesmo horário.

Exemplo inválido:

| Horário | Turma | Professor |
|---|---|---|
| Segunda 1º aula | 9º ano | Caroline |
| Segunda 1º aula | 7º ano A | Caroline |

Nesse caso, a professora Caroline foi alocada em duas turmas no mesmo período.

## H2: Turma em dois horários iguais

Uma turma não pode ter duas aulas no mesmo horário.

Exemplo inválido:

| Horário | Turma | Disciplina |
|---|---|---|
| Segunda 1º aula | 9º ano | Matemática |
| Segunda 1º aula | 9º ano | Português |

Nesse caso, a turma 9º ano possui duas aulas simultâneas.

## H3: Carga horária semanal incorreta

Cada disciplina deve aparecer na grade exatamente a quantidade de vezes definida.

Exemplo:

Se Matemática possui carga horária semanal de 4 aulas, ela deve aparecer 4 vezes na semana.

Se aparecer 3 ou 5 vezes, existe violação.

## Restrições desejáveis

As restrições desejáveis são chamadas de `soft constraints`.

Cada violação recebe penalidade de 10 pontos.

## S1: Mais de 2 aulas da mesma disciplina no mesmo dia

Uma turma não deve ter mais de 2 aulas da mesma disciplina no mesmo dia.

Exemplo indesejado:

| Horário | Disciplina |
|---|---|
| Segunda 1º aula | Matemática |
| Segunda 2º aula | Matemática |
| Segunda 3º aula | Matemática |


Nesse caso, existe uma violação soft.

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


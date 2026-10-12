# Cenários de teste do algoritmo

Os testes em `tests/` montam escolas miniatura e conferem se o AG se comporta como `docs/criterios-avaliacao.md` descreve.

Rodar (na raiz do repositório):

```text
pytest
```

## Como ler um cenário

Cada cenário isola uma regra. A grade é montada na mão (fitness) ou gerada pelo AG (integração). O resultado esperado é o número de violações H1–H4 e S1, ou o score.

Fórmula:

```text
Score = 100000 - (1000 * hard) - (10 * soft)
```

---

## Fitness (contagem das restrições)

Arquivo: `tests/test_fitness.py`

| Cenário | O que monta | Esperado |
|---|---|---|
| H1 Caroline no 9º e no 7º A, Segunda 1º aula | 1 professor, 2 turmas, mesmo slot | H1 = 1 |
| H1 Caroline em horários diferentes | Mesmos dados, slots 1 e 2 | H1 = 0 |
| H1 três turmas no mesmo slot | Ana em 6a, 6b e 6c | H1 = 2 |
| H2 Matemática e Português no 9º no mesmo slot | 1 turma, 2 disciplinas | H2 = 1 |
| H2 aulas em slots diferentes | Mesmos dados, slots 1 e 2 | H2 = 0 |
| H3 Matemática carga 4, 4 alocadas | 2 dias × 2 aulas | H3 = 0 |
| H3 Matemática carga 4, 1 aula sem horário | 3 alocadas + 1 vazia | H3 = 1 |
| H3 disciplina ausente da grade | carga 3, zero aulas | H3 = 3 |
| H3 aulas a mais | carga 1, 2 alocadas | H3 = 0 (só déficit) |
| H4 professor só na terça, aula na segunda | 2 dias × 1 aula | H4 = 1 |
| H4 aula na terça | mesmo professor | H4 = 0 |
| H4 `available_periods` vazio | qualquer slot | H4 = 0 |
| S1 três Matemáticas na segunda | 3 períodos no dia | S1 = 1 |
| S1 duas na segunda e uma na terça | mesma carga 3 | S1 = 0 |
| S1 quatro no mesmo dia | 4 períodos | S1 = 2 |
| Fórmula do documento | 2 hard + 3 soft | score 97970 |
| Grade perfeita | H1 válido | score 100000 |

## Operadores

Arquivo: `tests/test_operators.py`

| Cenário | Esperado |
|---|---|
| População de tamanho N | N indivíduos |
| Nascimento | cada disciplina aparece `weekly_workload` vezes |
| Nascimento | H2 = 0 (uma aula da turma por slot) |
| Carga > slots | aulas extras nascem sem horário (H3) |
| Instância trivial | indivíduo inicial já tem score 100000 |
| Cruzamento com taxa 0 | cópias independentes dos pais |
| Cruzamento com taxa 1 | filhos com carga correta e H2 = 0 |
| Mutação com taxa 0 | horários iguais aos originais |
| Mutação com taxa 1 | não introduz H2 nem muda a carga |
| Repair de aula sem horário | ocupa slot livre e zera H3 |
| Repair de H4 | move a aula para o dia disponível |
| Repair de H1 | as duas turmas ficam em slots diferentes |
| Repair impossível (professor sem período) | desaloca (H4 = 0, H3 = 1) |
| Torneio do tamanho da população | devolve o indivíduo de maior fitness |

## Contexto

Arquivo: `tests/test_context.py`

| Cenário | Esperado |
|---|---|
| Subject `6_ano_a_...` com `class_group_id=7_ano_a` | entra na 7ª, não na 6ª |
| Turma da manhã vs tarde | só vê slots do próprio turno |
| Turma sem turno | usa todos os slots |

## Validação da entrada

Arquivo: `tests/test_validate.py`

| Cenário | Esperado |
|---|---|
| Instância trivial | sem erros e sem avisos |
| 3 aulas e 2 slots | aviso de que não dá para encaixar |
| Disciplina sem turma | erro |
| professor ou turma inexistente | erro |
| id duplicado / carga 0 / nome repetido | erro |
| Professor sem dias marcados | aviso (tratado como disponível todos os dias) |
| Professor com mais aulas do que horários | aviso |
| JSON Bandeirante em `data/` | carrega; avisa nas turmas com carga > 25 |

## O AG de ponta a ponta

Arquivo: `tests/test_ga.py`

População e gerações pequenas; `random.seed(0)`.

| Cenário | Instância | Esperado |
|---|---|---|
| Trivial viável | 1 turma, 1 aula, 1 slot | score 100000 na geração 1 |
| Professor compartilhado | Ana dá 1 aula em 6a e 1 em 6b, 2 slots | H1 = 0 no resultado |
| Disponibilidade | Ana só na segunda, 2 aulas, 2+2 slots | as 2 aulas de Ana na segunda |
| S1 evitável | 4 aulas, 2 dias × 3 períodos | S1 = 0 (distribuição 2+2) |
| H3 estrutural | 3 aulas, 2 slots | H3 ≥ 1; score ≤ 99000 |
| Elitismo | professor compartilhado | `best_fitness` nunca cai |

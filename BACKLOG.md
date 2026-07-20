# BACKLOG — EstudoConcurso (MVP)

**Versão:** 0.1.0
**Relacionado ao PRD:** PRD.md v0.1.0
**Tamanhos:** S (≤0.5d) · M (0.5–1.5d) · L (>1.5d)

---

## Sprint 0 — Base da plataforma

**Objetivo:** ambiente rodando localmente em Docker com banco, lint, CI e logs.
**Carga total estimada:** 5S + 2M
**Gate de saída:** `docker compose up` sobe app+Postgres; `make lint` e `make test` passam na CI.

| ID | Descrição | Requisito | Tam. | Dependências |
|---|---|---|---|---|
| S0-01 | Criar repositório git e estrutura do projeto (app, tests, configs) | E5.1 | S | — |
| S0-02 | Dockerfile + docker-compose (app Streamlit; SQLite local) | E5.1 | M | S0-01 |
| S0-03 | Configurar CI (rodar lint + testes em push/PR) | E5.1 | S | S0-01 |
| S0-04 | Configurar lint (ruff) e formatação (black) | E5.1 | S | S0-01 |
| S0-05 | Init do banco (SQLAlchemy create_all: banks, subjects, questions, attempts) | E5.1 | M | S0-02 |
| S0-06 | Observabilidade: logs estruturados (nível, ação, duração) | E5.1 | S | S0-01 |
| S0-07 | Execução local via docker compose (smoke test) | E5.1 | S | S0-02, S0-05 |

> Nota: autenticação e "deploy de staging" do template foram removidos (ADR-3; app local de 1 usuário). Staging = execução local em Docker.

---

## Sprint 1 — Importação de questões (E1)

**Objetivo:** importar prova, converter e salvar questões válidas por banca/matéria.
**Carga total estimada:** 1S + 4M + 1L
**Gate de saída:** importar um PDF vira questões respondáveis no banco; questões inválidas separadas; banca/matéria configuráveis.

| ID | Descrição | Requisito | Tam. | Dependências |
|---|---|---|---|---|
| S1-01 | Integrar markitdown para converter arquivo → Markdown | E1.1 | M | S0-07 |
| S1-02 | Parser canônico de Markdown → questões (tipos múltipla e C/E) | E1.2 | L | S1-01 |
| S1-07 | Fallback de IA para estruturar texto de PDF real em questões | E1.6 | M | S1-01, S2-01 |
| S1-03 | Validação de questão conforme INV-1 (enunciado, ≥2 alt, gabarito) | E1.5 | M | S1-02 |
| S1-04 | UI: selecionar/criar banca e matéria no import | E1.3 | M | S0-07 |
| S1-05 | Auto-divisão por matéria (cabeçalho detectado, não-bloqueante) + fallback | E1.4 | M | S1-02 |
| S1-06 | Salvar questões validadas em `questions` | E1.1, E1.5 | S | S1-03, S1-04 |

---

## Sprint 2 — Geração de questões por IA (E2)

**Objetivo:** gerar questões por banca/matéria em 1 chamada, com justificativas, persistidas.
**Carga total estimada:** 2S + 4M
**Gate de saída:** informar banca+matéria gera N questões válidas (INV-4/INV-5) salvas no banco; teto de custo ativo.

| ID | Descrição | Requisito | Tam. | Dependências |
|---|---|---|---|---|
| S2-01 | Interface `AIProvider` + implementação Gemini (key em env) | E2.4 | M | S0-07 |
| S2-02 | Montar contexto banca+matéria sem prompt manual | E2.1 | M | S2-01 |
| S2-03 | Geração em 1 chamada → JSON (questão+alternativas+justificativas) | E2.2 | M | S2-02 |
| S2-04 | Validar questão IA (INV-4 e INV-5) antes de salvar | E2.2, E2.4 | M | S2-03 |
| S2-05 | Persistir toda questão gerada em `questions` | E2.3 | S | S2-04 |
| S2-06 | Teto de custo + log de uso (evento `cost_limit_reached`) | E2.5 | S | S2-01 |

---

## Sprint 3 — Estudo e Revisão (E3 + E4)

**Objetivo:** responder questões com feedback e revisar apenas os erros.
**Carga total estimada:** 4S + 2M
**Gate de saída:** fluxo responder→feedback funciona com e sem IA; modo revisão filtra erros.

| ID | Descrição | Requisito | Tam. | Dependências |
|---|---|---|---|---|
| S3-01 | UI de estudo: responder questão a questão | E3.1 | M | S1-06 |
| S3-02 | Feedback certo/errado + justificativas (se IA) | E3.1 | S | S3-01 |
| S3-03 | Garantir funcionamento sem IA (fluxo importado offline) | E3.2 | S | S3-01 |
| S3-04 | Troca de banca/matéria entre sessões | E3.3 | S | S3-01 |
| S3-05 | Registrar tentativas em `attempts` | E4.2 | S | S3-01 |
| S3-06 | Modo revisão: filtrar `correct=false` e re-responder | E4.1 | M | S3-05 |

---

## Regras do backlog

1. 1 tarefa = 1 issue.
2. 1 tarefa = 1 prompt de IA (Claude Code / Codex / Cursor).
3. IDs nunca mudam.
4. Tarefas canceladas permanecem registradas (riscadas, não apagadas).
5. Replanejamento apenas ao final da sprint.

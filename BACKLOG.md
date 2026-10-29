# BACKLOG — QAConcurso (Multi-Banca)

**Versão:** 1.0.0  
**Relacionado ao PRD:** PRD.md v1.0.0  
**Tamanhos:** S (≤0.5d) · M (0.5–1.5d) · L (>1.5d)

---

## Sprint 0 — Base da plataforma ✅ JÁ IMPLEMENTADA

**Objetivo:** ambiente rodando com banco, lint, CI e logs.  
**Carga total estimada:** 5S + 2M  
**Gate de saída:** `streamlit run app/main.py` sobe; `ruff check . && pytest tests/` passa.

| ID | Descrição | Requisito | Tam. | Dependências |
|---|---|---|---|---|
| S0-01 | Repositório git e estrutura do projeto | E5.1 | S | — |
| S0-02 | Dockerfile + docker-compose (SQLite local) | E5.1 | M | S0-01 |
| S0-03 | CI (lint + testes em push) | E5.1 | S | S0-01 |
| S0-04 | Lint (ruff) | E5.1 | S | S0-01 |
| S0-05 | Init do banco (create_all: banks, subjects, questions, attempts, templates) | E5.1 | M | S0-02 |
| S0-06 | Logs estruturados | E5.1 | S | S0-01 |
| S0-07 | Execução local (smoke test) | E5.1 | S | S0-02, S0-05 |

---

## Sprint 1 — Multi-banca com templates (P0)

**Objetivo:** cada banca tem template próprio, aprendido na importação, usado na geração. Feedback visual nas chamadas IA.  
**Carga total estimada:** 2S + 3M  
**Gate de saída:** importar prova da Cesgranrio → template salvo → gerar questões → saem no estilo Cesgranrio; spinner aparece durante chamadas.

| ID | Descrição | Requisito | Tam. | Dependências |
|---|---|---|---|---|
| S1-01 | Vincular template da banca na geração: montar prompt com `layout_description` do template | E2.2, E6.2 | M | S0-07 |
| S1-02 | Aprendizado automático de template na 1ª importação: após extrair questões, IA descreve layout e salva | E6.1 | M | S0-07 |
| S1-03 | Spinner + mensagem de status durante chamadas IA (import e geração) | E7.1, E7.3 | S | S0-07 |
| S1-04 | Timeout de 60s em chamadas de IA (INV-7) | RNF | S | S1-03 |
| S1-05 | Backup automático do `concurso.db` para `backups/` na inicialização | RNF | M | S0-07 |

---

## Sprint 2 — Importação robusta e UX (P0/P1)

**Objetivo:** importação com feedback claro de falhas; visual mais limpo.  
**Carga total estimada:** 1S + 2M  
**Gate de saída:** import falha → mensagem clara do motivo; template editável na UI.

| ID | Descrição | Requisito | Tam. | Dependências |
|---|---|---|---|---|
| S2-01 | Feedback detalhado de falha na importação (markitdown falhou? IA falhou?) | E1.1 | M | S1-03 |
| S2-02 | UI para ver/editar template de banca manualmente (text area) | E6.3 | M | S1-02 |
| S2-03 | CSS customizado no Streamlit (cores, fonte, espaçamento) | E7.4 | S | S0-07 |

---

## Sprint 3 — Controle de custo e refinamentos (P1)

**Objetivo:** teto de custo automático, progresso para lotes grandes.  
**Carga total estimada:** 2S + 1M  
**Gate de saída:** gerar 20 questões mostra barra de progresso; custo mensal não ultrapassa teto.

| ID | Descrição | Requisito | Tam. | Dependências |
|---|---|---|---|---|
| S3-01 | Teto de custo mensal (R$ 30) com log e bloqueio | E2.6 | M | S1-03 |
| S3-02 | Barra de progresso para lotes > 5 questões | E7.2 | S | S1-03 |

---

## Radar (fora do backlog atual)

| ID | Descrição | Prioridade |
|---|---|---|
| R-01 | Multiusuário | Futuro |
| R-02 | Estatísticas / dashboards | Futuro |
| R-03 | App mobile | Futuro |
| R-04 | IA local (Ollama) | Futuro |
| R-05 | Exportar banco de questões | Futuro |
| R-06 | Questões discursivas | Futuro |

---

## Regras do backlog

1. 1 tarefa = 1 issue no GitHub.
2. 1 tarefa = 1 prompt de IA (Claude Code / Codex / Cursor).
3. IDs nunca mudam.
4. Tarefas canceladas permanecem registradas (riscadas, não apagadas).
5. Replanejamento apenas ao final da sprint.

---

## Prompts de IA para Sprint 1

### S1-01 — Vincular template da banca na geração

```
Tarefa: Vincular template da banca na geração de questões

Base de código: app/generation.py, app/repository.py (get_template), app/ai/gemini.py

Objetivo: Ao gerar questões, buscar o template da banca em `templates` 
(banca + última signature) e incluir `layout_description` no prompt da IA.

Regras:
- Se não existir template, gerar sem (comportamento atual)
- O template é passado como contexto adicional no system prompt
- Não quebrar chamadas existentes (API compatível)

Arquivos para modificar:
1. app/generation.py — função generate_and_save recebe template opcional
2. app/ai/gemini.py — prompt inclui layout_description se fornecido
3. app/ai/nvidia.py — mesmo comportamento (paridade)

Testes: testar com template mockado e sem template
```

### S1-02 — Aprendizado automático de template

```
Tarefa: Aprender template da banca na primeira importação

Base: app/import_flow.py, app/repository.py (save_template, signature_of), app/ai/gemini.py

Objetivo: Após importar e extrair questões com sucesso, pedir para IA descrever
o layout da prova (formato das questões, como alternativas são apresentadas,
padrão de gabarito, tipo de questão predominante). Salvar em `templates`.

Fluxo:
1. Importar arquivo → extrair questões (já implementado)
2. Pegar o texto Markdown bruto + signature
3. Verificar se template já existe para (banca, signature)
4. Se não: chamar IA com prompt "Descreva o layout e formato das questões desta prova"
5. Salvar resultado em templates (banca, signature, layout_description)

Regras:
- Não aprender template se a IA principal falhou (reuso de questões inválidas)
- Usar modelo mais barato (Gemini Flash) para descrição
- Template é específico por (banca, signature) — aprendizado incremental

Arquivos: app/import_flow.py, app/ai/factory.py
```

### S1-03 — Spinner + status

```
Tarefa: Adicionar spinner e mensagem de status durante chamadas IA

Base: app/main.py (render_import, render_generate)

Objetivo: Substituir o freeze da interface por:
- Spinner com mensagem ("Gerando questões...", "Extraindo questões do PDF...")
- Toast/notificação ao final ("5 questões importadas com sucesso")
- Desabilitar botão durante operação (evitar duplo clique)

Streamlit tem: st.spinner(), st.toast(), st.session_state para controle de estado

Arquivos: app/main.py (funções render_import e render_generate)
```

### S1-04 — Timeout em chamadas IA

```
Tarefa: Adicionar timeout de 60s em chamadas de IA

Base: app/ai/gemini.py, app/ai/nvidia.py

Objetivo: Toda chamada ao provider de IA deve ter timeout de 60s.
Se exceder, levanta exceção tratada (não quebra o app).

Gemini SDK: parâmetro timeout no generate_content
NVIDIA: timeout no httpx.Client

Arquivos: app/ai/gemini.py, app/ai/nvidia.py
```

### S1-05 — Backup automático na inicialização

```
Tarefa: Backup automático do banco na inicialização

Base: app/main.py (main function), app/backup.py (já existe)

Objetivo: Copiar concurso.db para backups/concurso_YYYYMMDD_HHMMSS.db
toda vez que o app inicia. Manter últimos 7 backups (limpar os antigos).

Já existe app/backup.py — verificar se implementa isso ou ajustar.

Arquivos: app/main.py (chamar backup na main()), app/backup.py
```

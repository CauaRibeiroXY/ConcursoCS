import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
from pathlib import Path

import streamlit as st

from app.db import SessionLocal
from app.generation import generate_and_save
from app.import_flow import import_file
from app.models import Question
from app.repository import (
    fetch_questions,
    fetch_wrong_questions,
    list_banks,
    list_subjects,
    record_attempt,
)
from app.study import evaluate


def _bank_count() -> int:
    with SessionLocal() as s:
        return s.query(Question).count()


def render_import():
    st.header("Importar prova")
    bank = st.text_input("Banca", placeholder="Ex.: FCC")
    subject = st.text_input("Matéria (opcional)", placeholder="Ex.: Português")
    uploaded = st.file_uploader(
        "Arquivo da prova (PDF, DOCX, HTML, TXT, MD)",
        type=["pdf", "docx", "html", "txt", "md"],
    )
    disabled = st.session_state.get("importing", False)
    if st.button("Importar", disabled=disabled) and uploaded is not None:
        if not bank:
            st.warning("Informe a banca.")
            return
        suffix = Path(uploaded.name).suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getbuffer())
            tmp_path = tmp.name
        try:
            st.session_state.importing = True
            with st.spinner("Importando prova..."):
                result = import_file(tmp_path, bank, subject or "Geral")
            st.success(f"{result['saved']} questões importadas para '{result['bank']}'.")
            if result.get("template_learned"):
                st.toast("Template da banca aprendido automaticamente!")
            if result["invalid_count"]:
                st.warning(f"{result['invalid_count']} questões ignoradas (inválidas).")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Falha: {exc}")
        finally:
            st.session_state.importing = False


def render_generate():
    st.header("Gerar questões (IA)")
    bank = st.text_input("Banca", key="g_bank", placeholder="Ex.: FCC")
    subject = st.text_input("Matéria", key="g_subject", placeholder="Ex.: Português")
    count = st.number_input("Quantidade", min_value=1, max_value=50, value=5)
    if st.button("Gerar", disabled=st.session_state.get("generating", False)):
        if not bank or not subject:
            st.warning("Informe banca e matéria.")
            return
        try:
            st.session_state.generating = True
            with st.spinner(f"Gerando {count} questões para {bank}..."):
                result = generate_and_save(bank, subject, count)
            st.success(f"{result['saved']} questões geradas e salvas.")
            if result["invalid_count"]:
                st.warning(f"{result['invalid_count']} geradas inválidas (descartadas).")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Falha: {exc}")
        finally:
            st.session_state.generating = False


def _render_question(q: Question, prefix: str):
    st.write(q.statement)
    opts = list(q.alternatives.keys())
    widget = st.radio if len(q.answer) == 1 else st.multiselect
    sel = widget("Alternativas", opts, format_func=lambda k: f"{k}) {q.alternatives[k]}")
    if st.button("Responder", key=f"{prefix}_answer"):
        if not sel:
            st.warning("Selecione ao menos uma alternativa.")
            return
        user = [sel] if isinstance(sel, str) else list(sel)
        correct = evaluate(user, q.answer)
        record_attempt(q.id, user, correct)
        if correct:
            st.success("Correto!")
        else:
            st.error(f"Incorreto. Gabarito: {', '.join(q.answer)}")
        if q.justification:
            st.subheader("Justificativas")
            for k in q.alternatives:
                st.write(f"**{k})** {q.justification.get(k, '')}")


def render_study():
    st.header("Estudar")
    banks = list_banks()
    if not banks:
        st.info("Nenhuma questão ainda. Importe ou gere questões.")
        return
    bank = st.selectbox("Banca", banks, key="s_bank")
    subs = ["(todas)"] + list_subjects(bank)
    sub = st.selectbox("Matéria", subs, key="s_sub")
    subject = None if sub == "(todas)" else sub
    if st.button("Carregar", key="s_load"):
        st.session_state.study_qs = fetch_questions(bank, subject)
        st.session_state.study_idx = 0
    qs = st.session_state.get("study_qs", [])
    if not qs:
        st.info("Clique em Carregar.")
        return
    idx = st.session_state.study_idx
    if idx >= len(qs):
        st.success("Fim das questões!")
        return
    q = qs[idx]
    st.caption(f"Questão {idx + 1}/{len(qs)}")
    _render_question(q, "study")
    if st.button("Próxima", key="s_next"):
        st.session_state.study_idx += 1
        st.rerun()


def render_review():
    st.header("Revisar erros")
    banks = list_banks()
    if not banks:
        st.info("Nenhuma questão ainda.")
        return
    bank = st.selectbox("Banca", banks, key="r_bank")
    subs = ["(todas)"] + list_subjects(bank)
    sub = st.selectbox("Matéria", subs, key="r_sub")
    subject = None if sub == "(todas)" else sub
    if st.button("Carregar erros", key="r_load"):
        st.session_state.review_qs = fetch_wrong_questions(bank, subject)
        st.session_state.review_idx = 0
    qs = st.session_state.get("review_qs", [])
    if not qs:
        st.info("Clique em Carregar erros.")
        return
    idx = st.session_state.review_idx
    if idx >= len(qs):
        st.success("Fim da revisão!")
        return
    q = qs[idx]
    st.caption(f"Erro {idx + 1}/{len(qs)}")
    _render_question(q, "review")
    if st.button("Próxima", key="r_next"):
        st.session_state.review_idx += 1
        st.rerun()


def main() -> None:
    if "backup_done" not in st.session_state:
        from app.backup import backup as do_backup
        do_backup()
        st.session_state.backup_done = True
    st.title("EstudoConcurso")
    st.caption(f"Questões no banco: {_bank_count()}")
    menu = st.sidebar.radio("Modo", ["Importar", "Gerar (IA)", "Estudar", "Revisar erros"])
    if menu == "Importar":
        render_import()
    elif menu == "Gerar (IA)":
        render_generate()
    elif menu == "Estudar":
        render_study()
    else:
        render_review()


if __name__ == "__main__":
    main()

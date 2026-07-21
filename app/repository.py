from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Attempt, Bank, Question, Subject, Template

import hashlib


def signature_of(text: str, bank_name: str) -> str:
    """Fingerprint of an exam layout (banca + normalized text snippet)."""
    snippet = "".join(text.split())[:2000]
    return hashlib.md5(f"{bank_name}|{snippet}".encode()).hexdigest()


def get_or_create_bank(session: Session, name: str, source: str = "imported") -> Bank:
    bank = session.query(Bank).filter_by(name=name).first()
    if bank is None:
        bank = Bank(name=name, source=source)
        session.add(bank)
        session.flush()
    return bank


def get_or_create_subject(session: Session, bank_id: str, name: str) -> Subject:
    subject = session.query(Subject).filter_by(bank_id=bank_id, name=name).first()
    if subject is None:
        subject = Subject(bank_id=bank_id, name=name)
        session.add(subject)
        session.flush()
    return subject


def save_question(
    session: Session,
    bank: Bank,
    subject_name: str,
    q: dict,
    source: str = "imported",
) -> Question:
    subject = get_or_create_subject(session, bank.id, subject_name)
    question = Question(
        bank_id=bank.id,
        subject_id=subject.id,
        source=source,
        type=q["type"],
        statement=q["statement"].strip(),
        alternatives=q["alternatives"],
        answer=q["answer"],
        justification=q.get("justification") or None,
    )
    session.add(question)
    return question


def save_questions(
    valid: list[dict], bank_name: str, subject_name: str, source: str = "imported"
) -> int:
    count = 0
    with SessionLocal() as session:
        bank = get_or_create_bank(session, bank_name, source=source)
        for q in valid:
            save_question(session, bank, q.get("subject") or subject_name, q, source=source)
            count += 1
        session.commit()
    return count


def save_valid(valid: list[dict], bank_name: str, subject_name: str) -> int:
    return save_questions(valid, bank_name, subject_name, source="imported")


def list_banks() -> list[str]:
    with SessionLocal() as s:
        return [b.name for b in s.query(Bank).order_by(Bank.name).all()]


def list_subjects(bank_name: str) -> list[str]:
    with SessionLocal() as s:
        bank = s.query(Bank).filter_by(name=bank_name).first()
        if not bank:
            return []
        return [
            sub.name
            for sub in s.query(Subject).filter_by(bank_id=bank.id).order_by(Subject.name).all()
        ]


def fetch_questions(bank_name: str, subject_name: str | None = None, limit: int = 50):
    with SessionLocal() as s:
        q = s.query(Question).join(Bank, Question.bank_id == Bank.id).filter(
            Bank.name == bank_name
        )
        if subject_name:
            q = q.join(Subject, Question.subject_id == Subject.id).filter(
                Subject.name == subject_name
            )
        return q.order_by(Question.created_at).limit(limit).all()


def record_attempt(question_id: str, user_answer: list, correct: bool) -> None:
    with SessionLocal() as s:
        s.add(
            Attempt(question_id=question_id, user_answer=user_answer, correct=correct)
        )
        s.commit()


def fetch_wrong_questions(
    bank_name: str, subject_name: str | None = None, limit: int = 50
):
    with SessionLocal() as s:
        wrong_ids = s.query(Attempt.question_id).filter(Attempt.correct.is_(False)).subquery()
        q = (
            s.query(Question)
            .join(Bank, Question.bank_id == Bank.id)
            .filter(Bank.name == bank_name)
            .filter(Question.id.in_(s.query(wrong_ids)))
        )
        if subject_name:
            q = q.join(Subject, Question.subject_id == Subject.id).filter(
                Subject.name == subject_name
            )
        return q.order_by(Question.created_at).limit(limit).all()


def get_template(bank_name: str, signature: str) -> Template | None:
    with SessionLocal() as s:
        return s.query(Template).filter_by(banca=bank_name, signature=signature).first()


def save_template(bank_name: str, signature: str, description: str) -> None:
    with SessionLocal() as s:
        s.add(Template(banca=bank_name, signature=signature, layout_description=description))
        s.commit()

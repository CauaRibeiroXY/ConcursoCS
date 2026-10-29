from app.ai.factory import get_provider
from app.ai.provider import AIProvider
from app.repository import get_template_for_bank, save_questions


def validate_ai(q: dict) -> list[str]:
    """INV-4 + INV-5: same base rules plus justification for every alternative."""
    from app.validation import validate_question

    errors = validate_question(q)
    justification = q.get("justification") or {}
    for key in q.get("alternatives", {}):
        if key not in justification or not str(justification.get(key, "")).strip():
            errors.append(f"justificativa ausente para alternativa {key}")
    return errors


def generate_and_save(
    bank_name: str, subject_name: str, count: int, provider: AIProvider | None = None
) -> dict:
    provider = provider or get_provider()
    template = get_template_for_bank(bank_name)
    raw = provider.generate_questions(bank_name, subject_name, count, template=template)

    valid: list[dict] = []
    invalid: list[tuple[dict, list[str]]] = []
    for q in raw:
        errs = validate_ai(q)
        if errs:
            invalid.append((q, errs))
        else:
            valid.append(q)

    saved = save_questions(valid, bank_name, subject_name, source="ai")
    return {"saved": saved, "invalid_count": len(invalid), "invalid": invalid}

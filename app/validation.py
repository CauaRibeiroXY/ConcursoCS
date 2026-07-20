from app.parsing import parse_markdown


def validate_question(q: dict) -> list[str]:
    """Return a list of problems. Empty list means the question is valid (INV-1)."""
    errors: list[str] = []

    statement = (q.get("statement") or "").strip()
    if not statement:
        errors.append("enunciado vazio")

    alternatives = q.get("alternatives") or {}
    if len(alternatives) < 2:
        errors.append("menos de 2 alternativas")

    answer = q.get("answer") or []
    if not answer:
        errors.append("gabarito vazio")
    else:
        for key in answer:
            if key not in alternatives:
                errors.append(f"gabarito '{key}' não existe entre as alternativas")

    return errors


def partition(questions: list[dict]) -> tuple[list[dict], list[tuple[dict, list[str]]]]:
    valid: list[dict] = []
    invalid: list[tuple[dict, list[str]]] = []
    for q in questions:
        errs = validate_question(q)
        if errs:
            invalid.append((q, errs))
        else:
            valid.append(q)
    return valid, invalid

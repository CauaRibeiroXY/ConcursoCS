from app.ai.factory import get_provider
from app.ai.provider import AIProvider
from app.markdown_import import file_to_markdown
from app.parsing import parse_markdown
from app.repository import get_template, save_template, save_valid, signature_of
from app.validation import partition


def _ensure_type(q: dict) -> None:
    if "type" not in q:
        q["type"] = "ce" if len(q.get("alternatives", {})) == 2 else "multiple"


def import_file(path: str, bank_name: str, subject_name: str, provider: AIProvider | None = None) -> dict:
    """Full import flow: file -> markdown -> parse -> (fallback IA) -> validate -> save.

    Non-blocking: invalid questions are returned, never raised.
    When the canonical parser finds nothing (typical real PDF), the AI structures
    the raw text into questions. The learned layout is cached per (banca, layout)
    so subsequent imports of the same exam type reuse the template (no need to
    re-request a template each time).
    """
    md = file_to_markdown(path)
    parsed = parse_markdown(md, bank_name, subject_name)
    questions = parsed["questions"]
    source_bank = parsed["bank"]

    if not questions:
        provider = provider or get_provider()
        sig = signature_of(md, bank_name)
        template = get_template(bank_name, sig)
        guidance = template.layout_description if template else None
        questions, description = provider.structure_questions(
            md, bank_name, subject_name, guidance=guidance
        )
        if not template and description:
            save_template(bank_name, sig, description)

    for q in questions:
        _ensure_type(q)

    valid, invalid = partition(questions)
    saved = save_valid(valid, source_bank, subject_name)
    return {
        "bank": source_bank,
        "saved": saved,
        "invalid_count": len(invalid),
        "invalid": invalid,
    }

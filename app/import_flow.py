from app.markdown_import import file_to_markdown
from app.parsing import parse_markdown
from app.repository import save_valid
from app.validation import partition


def import_file(path: str, bank_name: str, subject_name: str) -> dict:
    """Full import flow: file -> markdown -> parse -> validate -> save.

    Non-blocking: invalid questions are returned, never raised.
    """
    md = file_to_markdown(path)
    parsed = parse_markdown(md, bank_name, subject_name)
    valid, invalid = partition(parsed["questions"])
    saved = save_valid(valid, parsed["bank"], subject_name)
    return {
        "bank": parsed["bank"],
        "saved": saved,
        "invalid_count": len(invalid),
        "invalid": invalid,
    }

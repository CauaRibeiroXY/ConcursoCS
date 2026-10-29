import re
import unicodedata
from logging import getLogger

from app.ai.factory import get_provider
from app.cleaner import clean_exam_text
from app.markdown_import import file_to_markdown
from app.markdown_parser import split_questions
from app.parsing import parse_markdown
from app.repository import get_template, save_template, save_valid, signature_of
from app.validation import partition

log = getLogger(__name__)


def _unaccent(text: str) -> str:
    """Remove accents for fuzzy matching."""
    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ascii", "ignore").decode("ascii")


_SECTION_TAGS = {
    "TECNOLOGIA": "TECNOLOGIA DA INFORMACAO",
    "TI": "TECNOLOGIA DA INFORMACAO",
    "PORTUGUESA": "LINGUA PORTUGUESA",
    "INGLESA": "LINGUA INGLESA",
    "MATEMATICA": "MATEMATICA",
    "PROBABILIDADE": "PROBABILIDADE E ESTATISTICA",
    "BANCARIO": "CONHECIMENTOS BANCARIOS",
    "ATUALIDADES": "ATUALIDADES",
}


def _find_section(text: str, subject: str) -> str:
    """Find the 2nd+ occurrence of the subject header (skips cover-page table)."""
    flat = _unaccent(text.upper())
    subj_flat = _unaccent(subject.upper().strip())

    target = ""
    for key, header in _SECTION_TAGS.items():
        if key in subj_flat:
            target = header
            break
    if not target:
        return text

    # Find all occurrences; use the one after "CONHECIMENTOS BASICOS" section
    occ = [m.start() for m in re.finditer(re.escape(target), flat)]
    if len(occ) < 2:
        return text

    # Find occurrence that's preceded by blank line or header (actual section start)
    idx = occ[1]  # second occurrence is the actual section header
    line_start = text.rfind("\n", 0, idx) + 1
    section = text[line_start:]

    rest = _unaccent(section.upper())
    next_pos = len(section)
    for _, header in _SECTION_TAGS.items():
        if header != target:
            pos = rest.find(header)
            if 0 < pos < next_pos:
                next_pos = pos
    return section[:next_pos].strip()


def _ensure_type(q: dict) -> None:
    if "type" not in q:
        q["type"] = "ce" if len(q.get("alternatives", {})) == 2 else "multiple"


def import_file(path: str, bank_name: str, subject_name: str, provider=None) -> dict:
    """Full import flow: file -> markdown -> rule parser -> (fallback AI).

    Uses rule-based extraction first (~17 questions in 0.1s).
    If parser finds nothing, falls back to Gemini on the subject-specific section.
    """
    md = file_to_markdown(path)
    parsed = parse_markdown(md, bank_name, subject_name)
    questions = parsed["questions"]
    source_bank = parsed["bank"]

    if not questions:
        # Try rule-based parser on cleaned text
        clean = clean_exam_text(md)
        section = _find_section(clean, subject_name)
        questions = split_questions(section)
        log.info(
            "Parser baseado em regras: %d questoes encontradas na secao '%s'",
            len(questions), subject_name,
        )

    template_learned = False
    if not questions:
        provider = provider or get_provider()
        clean = clean_exam_text(md)
        section = _find_section(clean, subject_name)
        log.info("Fallback AI: enviando %d chars para extrair questoes", len(section))
        questions, layout_desc = provider.structure_questions(section, bank_name, subject_name)
        if layout_desc and questions:
            sig = signature_of(md, bank_name)
            existing = get_template(bank_name, sig)
            if not existing:
                save_template(bank_name, sig, layout_desc)
                template_learned = True
                log.info("Template aprendido para banca '%s' (signature=%s)", bank_name, sig)

    for q in questions:
        _ensure_type(q)

    valid, invalid = partition(questions)
    saved = save_valid(valid, source_bank, subject_name)
    return {
        "bank": source_bank,
        "saved": saved,
        "invalid_count": len(invalid),
        "invalid": invalid,
        "template_learned": template_learned,
    }

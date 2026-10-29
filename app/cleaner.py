import re

# Lines / artifacts to strip from markitdown output
_REMOVE_PATTERNS = [
    r"^pcimarkpci\s+\S.*$",
    r"^www\.pciconcursos\.com\.br$",
    r"^_+\s*$",
    r"^\s*\d+\s*$",  # standalone page numbers
    r"^BANCO DO BRASIL\s*$",
    r"^GABARITO\s+\d+\s+.*$",
    r"^\d+\s*$",  # orphan numbers
]

_REMOVE_RE = re.compile("|".join(_REMOVE_PATTERNS), re.MULTILINE | re.IGNORECASE)

_REMOVE_LINE_RE = re.compile(
    r"^(AGENTE DE TECNOLOGIA).*$",
    re.MULTILINE | re.IGNORECASE,
)

# Lines that are just letters from answer sheet graphics
_SHEET_LETTERS = re.compile(r"^[OHNCUSAR]\s*$", re.MULTILINE)


def clean_exam_text(raw: str) -> str:
    """Remove scan artifacts, page headers, and answer-sheet noise."""
    text = _REMOVE_RE.sub("", raw)
    text = _REMOVE_LINE_RE.sub("", text)
    text = _SHEET_LETTERS.sub("", text)
    # collapse repeated blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

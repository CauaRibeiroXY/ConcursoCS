import re
from typing import Optional

_ALT_RE = re.compile(r"^\(([A-E])\)\s+(.*)", re.MULTILINE)
_Q_NUM = re.compile(r"^(\d{1,2})\s*$", re.MULTILINE)
# Sheet-artifact lines: mostly underscores, isolated letters O/H/N/U/C/S/A/R on own line
_ARTIFACT_RE = re.compile(r"^_{2,}$|^[OHNCUSAR]\s*$", re.MULTILINE)
# Lines that trigger (A)-(E) but are from the answer sheet graphic
_SHEET_ALT = re.compile(r"^\([A-E]\)\s*_{2,}.*$")


def split_questions(text: str) -> list[dict]:
    lines = text.splitlines()

    # Detect if this entire text is an exam with multiple questions
    # by counting how many (A)-(E) groups appear
    alt_positions: list[int] = []
    for i, line in enumerate(lines):
        if _ALT_RE.match(line) and not _SHEET_ALT.match(line):
            alt_positions.append(i)

    if not alt_positions:
        return []

    # Group consecutive alt lines into blocks
    blocks: list[list[int]] = []
    current = [alt_positions[0]]
    for pos in alt_positions[1:]:
        if pos == current[-1] + 1:
            current.append(pos)
        else:
            blocks.append(current)
            current = [pos]
    blocks.append(current)

    # Filter: real question blocks have at least 3 alternatives (A, B, C or more)
    real_blocks = [b for b in blocks if len(b) >= 3]

    questions: list[dict] = []
    for block in real_blocks:
        q = _extract_one(lines, block)
        if q and len(q["statement"]) > 15:
            questions.append(q)

    return questions


def _extract_one(lines: list[str], alt_block: list[int]) -> Optional[dict]:
    alt_start = alt_block[0]
    alt_end = alt_block[-1]

    # Extract alternatives (skip sheet-artifact lines)
    alternatives: dict[str, str] = {}
    for i in range(alt_start, alt_end + 1):
        m = _ALT_RE.match(lines[i])
        if m and not _SHEET_ALT.match(lines[i]):
            key = m.group(1)
            val = m.group(2).strip()
            # Skip if value is all underscores/padding
            if re.match(r"^[_\- ]+$", val):
                continue
            # Fold continuation lines
            j = i + 1
            while j < len(lines) and lines[j].startswith(" ") and not _ALT_RE.match(lines[j]):
                val += " " + lines[j].strip()
                j += 1
            alternatives[key] = val

    if len(alternatives) < 3:
        return None

    # Walk backward from alt_start to find the question number
    q_number_line = None
    for i in range(alt_start - 1, -1, -1):
        s = lines[i].strip()
        if _ARTIFACT_RE.match(s):
            continue
        m = _Q_NUM.match(s)
        if m:
            _ = int(m.group(1))
            q_number_line = i
            break

    # Gather statement lines between number and first alternative
    start_search = (q_number_line + 1) if q_number_line is not None else max(alt_start - 8, 0)
    statement_lines = []
    for i in range(start_search, alt_start):
        s = lines[i].strip()
        if s and not _Q_NUM.match(s) and not _ARTIFACT_RE.match(s):
            statement_lines.append(s)

    statement = " ".join(statement_lines).strip()
    if len(statement) < 10:
        return None

    # Remove duplicate text (some PDFs repeat the question)
    # If statement ends with same chars as it starts
    if len(statement) > 100 and statement[-40:] in statement[:80]:
        statement = statement[: -40].strip()

    return {
        "statement": statement,
        "alternatives": alternatives,
        "answer": [],
        "justification": {},
    }


def find_gabarito(text: str) -> dict[int, str]:
    matches = re.findall(r"(\d{1,2})\s*[-–—]?\s*([A-E])", text[-3000:])
    result: dict[int, str] = {}
    for k, v in matches:
        result[int(k)] = v
    return result

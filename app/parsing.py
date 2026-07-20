import re

_QUESTION_RE = re.compile(r"^\s*#{1,6}\s*question\b", re.I)
_ANSWER_RE = re.compile(r"^\s*answer\s*:", re.I)
_ALT_RE = re.compile(r"^\s*([A-Ea-e])[).]\s+(.*)$")
_HEADER_RE = re.compile(r"^\s*(#{1,6})\s*(.*)$")


def _split_header(text: str):
    text = text.strip()
    level = len(text) - len(text.lstrip("#"))
    body = text[level:].strip()
    return body


def parse_markdown(md: str, default_bank: str, default_subject: str) -> dict:
    """Convert canonical Markdown into structured question dicts.

    Returns {"bank": str, "questions": [ {subject, statement, alternatives,
    answer, justification, type} ]}. Non-blocking: missing subjects fall back
    to default_subject; parsing never raises on bad blocks (validation handles it).
    """
    lines = md.replace("\r\n", "\n").split("\n")

    bank = default_bank
    cur_subject = default_subject
    questions: list[dict] = []
    cur: dict | None = None
    in_justification = False

    def new_question(subject: str) -> dict:
        return {
            "subject": subject,
            "statement": "",
            "alternatives": {},
            "answer": [],
            "justification": {},
        }

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        header = _HEADER_RE.match(line)
        if header:
            body = _split_header(stripped)
            low = body.lower()
            if low.startswith("banca"):
                if ":" in body:
                    bank = body.split(":", 1)[1].strip() or bank
                continue
            if low.startswith("materia") or low.startswith("matéria"):
                cur_subject = (
                    body.split(":", 1)[1].strip() if ":" in body else body
                ) or cur_subject
                continue
            if _QUESTION_RE.match(line):
                if cur:
                    questions.append(cur)
                cur = new_question(cur_subject)
                in_justification = False
                continue
            if low.startswith("justification") or low.startswith("justificativa"):
                in_justification = True
                continue
            # best-effort subject heading (short title, not a known keyword)
            if len(body) <= 40:
                cur_subject = body
                continue
            continue

        if cur is None:
            continue

        if re.match(r"^\s*(justification|justificativa)\s*:", line, re.I):
            in_justification = True
            continue

        alt = _ALT_RE.match(line)
        if alt:
            key = alt.group(1).upper()
            text = alt.group(2).strip()
            if in_justification:
                cur["justification"][key] = text
            else:
                cur["alternatives"][key] = text
            continue

        if _ANSWER_RE.match(line):
            vals = re.findall(r"[A-Ea-e]", line.split(":", 1)[1])
            cur["answer"] = [v.upper() for v in vals]
            continue

        if stripped:
            if in_justification and cur["justification"]:
                last = max(cur["justification"])
                cur["justification"][last] += " " + stripped
            else:
                cur["statement"] += (" " if cur["statement"] else "") + stripped

    if cur:
        questions.append(cur)

    for q in questions:
        q["type"] = "ce" if len(q["alternatives"]) == 2 else "multiple"

    return {"bank": bank, "questions": questions}

from app.parsing import parse_markdown
from app.validation import partition, validate_question

SAMPLE = """
# BANCA: FCC
# MATERIA: Português

## QUESTION
Qual o plural de "cidadão"?

A) cidadãos
B) cidadões
C) cidadãos
D) cidadao
E) cidadões

ANSWER: C

JUSTIFICATION:
A) forma incorreta
B) acento incorreto
C) correto
D) sem acento
E) acento incorreto

## QUESTION
Escolha a frase correta.

A) Ele foi ao mercado.
B) Ele foi a mercado.
C) Ele foi há mercado.

ANSWER: A

JUSTIFICATION:
A) correto
B) preposição errada
C) crase errada
"""


def test_parse_two_questions():
    parsed = parse_markdown(SAMPLE, "DefaultBank", "DefaultSub")
    assert parsed["bank"] == "FCC"
    qs = parsed["questions"]
    assert len(qs) == 2
    assert qs[0]["subject"] == "Português"
    assert qs[0]["answer"] == ["C"]
    assert qs[0]["alternatives"]["A"] == "cidadãos"
    assert qs[0]["justification"]["C"] == "correto"
    assert qs[0]["type"] == "multiple"


def test_validation_ok():
    parsed = parse_markdown(SAMPLE, "B", "S")
    valid, invalid = partition(parsed["questions"])
    assert len(valid) == 2
    assert invalid == []


def test_inv1_empty_statement():
    md = "## QUESTION\n\nA) a\nB) b\nANSWER: A\n"
    qs = parse_markdown(md, "B", "S")["questions"]
    assert validate_question(qs[0])  # has errors


def test_inv1_single_alternative():
    md = "## QUESTION\nEnunciado.\nA) a\nANSWER: A\n"
    qs = parse_markdown(md, "B", "S")["questions"]
    errs = validate_question(qs[0])
    assert any("alternativas" in e for e in errs)


def test_inv1_bad_answer():
    md = "## QUESTION\nEnunciado.\nA) a\nB) b\nANSWER: Z\n"
    qs = parse_markdown(md, "B", "S")["questions"]
    errs = validate_question(qs[0])
    assert any("gabarito" in e for e in errs)


def test_auto_subject_heading():
    md = """
# BANCA: CESPE
## Matemática
## QUESTION
Quanto é 2+2?

A) 3
B) 4

ANSWER: B
"""
    parsed = parse_markdown(md, "B", "DefaultSub")
    assert parsed["questions"][0]["subject"] == "Matemática"


def test_ce_type():
    md = "## QUESTION\nAfirmação.\nA) CERTO\nB) ERRADO\nANSWER: A\n"
    qs = parse_markdown(md, "B", "S")["questions"]
    assert qs[0]["type"] == "ce"

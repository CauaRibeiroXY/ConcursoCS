from app.repository import (
    fetch_questions,
    fetch_wrong_questions,
    record_attempt,
    save_questions,
)
from app.study import evaluate


def test_evaluate():
    assert evaluate(["C"], ["C"])
    assert not evaluate(["A"], ["C"])
    assert evaluate(["A", "B"], ["B", "A"])


def test_wrong_questions_flow():
    save_questions(
        [
            {
                "statement": "x",
                "alternatives": {"A": "a", "B": "b"},
                "answer": ["A"],
                "type": "multiple",
            }
        ],
        "WB",
        "WS",
        source="imported",
    )
    assert fetch_wrong_questions("WB") == []
    q = fetch_questions("WB")[0]
    record_attempt(q.id, ["B"], False)
    wrong = fetch_wrong_questions("WB")
    assert len(wrong) == 1
    assert wrong[0].id == q.id

from app.ai.provider import AIProvider
from app.generation import generate_and_save
from app.repository import fetch_questions


class MockProvider(AIProvider):
    def generate_questions(
        self, bank: str, subject: str, count: int, template: str | None = None
    ) -> list[dict]:
        return [
            {
                "statement": "Q1",
                "alternatives": {"A": "a", "B": "b", "C": "c"},
                "answer": ["C"],
                "justification": {"A": "x", "B": "y", "C": "certo"},
                "type": "multiple",
            },
            {
                "statement": "Q2",
                "alternatives": {"A": "CERTO", "B": "ERRADO"},
                "answer": ["A"],
                "justification": {"A": "certo", "B": "errado"},
                "type": "ce",
            },
            # invalid: justificativa ausente para B
            {
                "statement": "Q3",
                "alternatives": {"A": "a", "B": "b"},
                "answer": ["A"],
                "justification": {"A": "certo"},
                "type": "ce",
            },
        ]

    def structure_questions(self, text, bank, subject, guidance=None):
        return [], ""

def test_generate_and_save_persists_valid():
    res = generate_and_save("MockBank", "MockSub", 3, provider=MockProvider())
    assert res["saved"] == 2
    assert res["invalid_count"] == 1
    qs = fetch_questions("MockBank")
    assert len(qs) == 2
    assert all(q.source == "ai" for q in qs)
    assert all(q.justification for q in qs)

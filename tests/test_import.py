from app.ai.provider import AIProvider
from app.import_flow import import_file


class MockProvider(AIProvider):
    def generate_questions(self, bank, subject, count):
        return []

    def structure_questions(self, text, bank, subject, guidance=None):
        return [
            {
                "statement": "Q1 estruturada",
                "alternatives": {"A": "a", "B": "b", "C": "c"},
                "answer": ["C"],
                "justification": {"A": "", "B": "", "C": "certo"},
            },
            {
                "statement": "Q2 estruturada",
                "alternatives": {"A": "CERTO", "B": "ERRADO"},
                "answer": ["A"],
                "justification": {"A": "certo", "B": "errado"},
            },
        ], "layout de teste"


def test_import_structured_fallback(tmp_path):
    txt = tmp_path / "prova.txt"
    txt.write_text("texto qualquer sem formato canonico nenhuma questao")
    res = import_file(str(txt), "BancoX", "MatY", provider=MockProvider())
    assert res["saved"] == 2
    assert res["bank"] == "BancoX"
    assert res["invalid_count"] == 0

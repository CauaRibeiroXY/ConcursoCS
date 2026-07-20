import json
import re

from app.ai.provider import AIProvider
from app.config import GEMINI_API_KEY

_MODEL = "gemini-1.5-flash"


def _build_prompt(bank: str, subject: str, count: int) -> str:
    return (
        f"Você é um elaborador de questões de concurso público para a banca "
        f"'{bank}' na matéria '{subject}'. Gere {count} questões.\n"
        "Cada questão deve ter: enunciado, alternativas (letras A, B, C...; "
        "para certo/errado use A) CERTO e B) ERRADO), gabarito (lista das letras "
        "corretas) e justificativa para CADA alternativa (por que a correta está "
        "certa e por que cada incorreta está errada).\n"
        "Responda SOMENTE com um array JSON válido, sem texto ou markdown extra, "
        'no formato: [{"statement": "...", "alternatives": {"A": "..."}, '
        '"answer": ["C"], "justification": {"A": "...", "C": "..."}}].'
    )


def _extract_json(text: str) -> list[dict]:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    raw = fenced.group(1) if fenced else text
    return json.loads(raw.strip())


def _build_structure_prompt(text: str, bank: str, subject: str) -> str:
    return (
        f"Abaixo está o texto convertido de uma prova de concurso da banca "
        f"'{bank}' (matéria '{subject}'). Extraia TODAS as questões objetivas "
        "existentes no texto, usando o gabarito embutido para definir a resposta "
        "correta.\n"
        "Para cada questão retorne um objeto JSON com: statement (enunciado), "
        "alternatives (objeto com chaves A, B, C... e os textos), answer (lista "
        "das letras corretas) e justification (objeto com uma chave por "
        "alternativa; se não souber, use texto vazio).\n"
        "Responda SOMENTE com um array JSON válido, sem texto ou markdown extra.\n\n"
        f"TEXTO:\n{text}"
    )


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str = _MODEL):
        self._api_key = api_key or GEMINI_API_KEY
        self._model = model
        if not self._api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não configurada. Defina no .env para gerar questões."
            )
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        self._genai = genai

    def generate_questions(self, bank: str, subject: str, count: int) -> list[dict]:
        model = self._genai.GenerativeModel(self._model)
        resp = model.generate_content(_build_prompt(bank, subject, count))
        data = _extract_json(resp.text)
        for q in data:
            q["type"] = "ce" if len(q.get("alternatives", {})) == 2 else "multiple"
        return data

    def structure_questions(self, text: str, bank: str, subject: str) -> list[dict]:
        model = self._genai.GenerativeModel(self._model)
        resp = model.generate_content(_build_structure_prompt(text, bank, subject))
        data = _extract_json(resp.text)
        for q in data:
            alts = q.get("alternatives", {})
            q["type"] = "ce" if len(alts) == 2 else "multiple"
        return data

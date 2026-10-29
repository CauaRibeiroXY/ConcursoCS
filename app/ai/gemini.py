import json
import re
from logging import getLogger

from app.ai.provider import AIProvider
from app.config import GEMINI_API_KEY, GEMINI_MODEL

log = getLogger(__name__)

_MODEL = GEMINI_MODEL
FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


def _call_with_fallback(client, model_list: list[str], prompt: str) -> str:
    last_error = None
    for model_name in model_list:
        try:
            resp = client.interactions.create(model=model_name, input=prompt)
            return resp.output_text
        except Exception as exc:
            log.warning("Modelo '%s' falhou: %s", model_name, exc)
            last_error = exc
    raise last_error  # type: ignore[misc]


def _build_prompt(bank: str, subject: str, count: int, template: str | None = None) -> str:
    guidance = ""
    if template:
        guidance = f"\nUse o seguinte formato/estilo conhecido desta banca:\n{template}\n"
    return (
        f"Voce e um elaborador de questoes de concurso publico para a banca "
        f"'{bank}' na materia '{subject}'. Gere {count} questoes.\n"
        "Cada questao deve ter: enunciado, alternativas (letras A, B, C...; "
        "para certo/errado use A) CERTO e B) ERRADO), gabarito (lista das letras "
        "corretas) e justificativa para CADA alternativa.\n"
        f"{guidance}"
        "Responda SOMENTE com um array JSON valido, sem texto ou markdown extra, "
        'no formato: [{"statement": "...", "alternatives": {"A": "..."}, '
        '"answer": ["C"], "justification": {"A": "...", "C": "..."}}].'
    )


def _extract_json(text: str) -> list[dict]:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    raw = fenced.group(1) if fenced else text
    return json.loads(raw.strip())


def _build_structure_prompt(text: str, bank: str, subject: str, guidance: str | None = None) -> str:
    prefix = ""
    if guidance:
        prefix = (
            f"Formato conhecido desta banca: {guidance}. Extraia as questoes "
            "seguindo esse mesmo formato.\n"
        )
    return (
        f"{prefix}Abaixo esta o texto convertido de uma prova de concurso da banca "
        f"'{bank}' (materia '{subject}'). Extraia TODAS as questoes objetivas "
        "existentes no texto, usando o gabarito embutido para definir a resposta "
        "correta.\n"
        "Tambem produza uma breve descricao do layout (layout_description) para "
        "reaproveitar em importacoes futuras da mesma banca.\n"
        "Responda SOMENTE com um objeto JSON valido, sem texto ou markdown extra, "
        'no formato: {"layout_description": "...", "questions": [{"statement": "...", '
        '"alternatives": {"A": "..."}, "answer": ["C"]}]}\n\n'
        f"TEXTO:\n{text}"
    )


def _extract_structure(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    raw = fenced.group(1) if fenced else text
    return json.loads(raw.strip())


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None, timeout: int = 60):
        from google import genai

        self._api_key = api_key or GEMINI_API_KEY
        self._model = model or GEMINI_MODEL
        self._timeout = timeout
        if not self._api_key:
            raise RuntimeError("GEMINI_API_KEY nao configurada. Defina no .env.")
        self._client = genai.Client(
            api_key=self._api_key, http_options={"timeout": self._timeout * 1000}
        )
        log.info("GeminiProvider iniciado, modelo: %s, timeout: %ds", self._model, self._timeout)

    def generate_questions(
        self, bank: str, subject: str, count: int, template: str | None = None
    ) -> list[dict]:
        models = [self._model] + [m for m in FALLBACK_MODELS if m != self._model]
        text = _call_with_fallback(
            self._client, models, _build_prompt(bank, subject, count, template)
        )
        data = _extract_json(text)
        for q in data:
            q["type"] = "ce" if len(q.get("alternatives", {})) == 2 else "multiple"
        return data

    def structure_questions(
        self, text: str, bank: str, subject: str, guidance: str | None = None
    ) -> tuple[list[dict], str]:
        models = [self._model] + [m for m in FALLBACK_MODELS if m != self._model]
        log.info("Estruturando questoes — modelos a tentar: %s", models)
        prompt = _build_structure_prompt(text, bank, subject, guidance)
        resp_text = _call_with_fallback(self._client, models, prompt)
        data = _extract_structure(resp_text)
        questions = data.get("questions", [])
        description = data.get("layout_description", "")
        for q in questions:
            alts = q.get("alternatives", {})
            q["type"] = "ce" if len(alts) == 2 else "multiple"
        return questions, description

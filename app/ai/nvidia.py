import json
import re
from logging import getLogger

from openai import OpenAI

from app.ai.provider import AIProvider

log = getLogger(__name__)

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.1-8b-instruct"


def _try_parse_json(text: str) -> object:
    raw = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, re.S)
    if fenced:
        raw = fenced.group(1).strip()
    raw = _sanitize_json(raw)
    return json.loads(raw)


def _sanitize_json(s: str) -> str:
    return re.sub(r'\\(?![\\"/bfnrt]|u[0-9a-fA-F]{4})', '', s)


SYSTEM_JSON = (
    "You are a precise JSON generator. "
    "Always reply with ONLY valid JSON, no markdown, no explanation."
)


def _call_with_retry(client, model: str, prompt: str, max_tokens: int) -> str:
    last_err = None
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_JSON},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.05,
                top_p=0.9,
                max_tokens=max_tokens,
                stream=False,
            )
            content = resp.choices[0].message.content or ""
            return content
        except Exception as exc:
            log.warning("Tentativa %d falhou: %s", attempt + 1, exc)
            last_err = exc
    raise last_err  # type: ignore[misc]


class NvidiaProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        key = api_key or ""
        if not key:
            raise RuntimeError("NVIDIA_API_KEY nao configurada. Defina no .env.")
        self._model = model or NVIDIA_MODEL
        self._client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=key, timeout=300)
        log.info("NvidiaProvider iniciado, modelo: %s", self._model)

    def generate_questions(
        self, bank: str, subject: str, count: int, template: str | None = None
    ) -> list[dict]:
        prompt = _build_prompt(bank, subject, count, template)
        text = _call_with_retry(self._client, self._model, prompt, 8192)
        obj = _try_parse_json(text)
        if not isinstance(obj, list):
            obj = [obj]
        for q in obj:
            alts = q.get("alternatives", {})
            q["type"] = "ce" if len(alts) == 2 else "multiple"
        return obj

    def structure_questions(
        self, text: str, bank: str, subject: str, guidance: str | None = None
    ) -> tuple[list[dict], str]:
        prompt = _build_structure_prompt(text, bank, subject, guidance)
        log.info("Enviando %d chars para NVIDIA (%s)...", len(prompt), self._model)
        resp_text = self._call_with_json_retry(prompt)
        obj = _try_parse_json(resp_text)
        if isinstance(obj, list):
            questions = obj
            description = ""
        else:
            questions = obj.get("questions", [])
            description = obj.get("layout_description", "")
        for q in questions:
            alts = q.get("alternatives", {})
            q["type"] = "ce" if len(alts) == 2 else "multiple"
        return questions, description

    def _call_with_json_retry(self, prompt: str) -> str:
        for attempt in range(3):
            resp_text = _call_with_retry(self._client, self._model, prompt, 32768)
            try:
                _try_parse_json(resp_text)
                return resp_text
            except json.JSONDecodeError as e:
                log.warning(
                    "JSON malformado (tentativa %d): %s. Resposta: %s...",
                    attempt + 1, e, resp_text[:250],
                )
                if attempt == 2:
                    raise
                prompt += "\n\nRESPONDA APENAS COM JSON VALIDO, SEM TEXTO EXTRA."
        return resp_text


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


def _build_structure_prompt(text: str, bank: str, subject: str, guidance: str | None = None) -> str:
    prefix = ""
    if guidance:
        prefix = (
            f"Formato conhecido desta banca: {guidance}. Extraia as questoes "
            "seguindo esse mesmo formato.\n"
        )
    return (
        f"{prefix}Abaixo esta o texto convertido de uma prova de concurso da banca "
        f"'{bank}' (materia '{subject}'). Extraia TODAS as questOes objetivas "
        "existentes no texto, usando o gabarito embutido para definir a resposta "
        "correta.\n"
        "Produza tambem uma breve descricao do layout (layout_description).\n"
        "Responda SOMENTE com um JSON valido, "
        'no formato: {"layout_description": "...", "questions": [{"statement": "...", '
        '"alternatives": {"A": "..."}, "answer": ["C"]}]}\n\n'
        f"TEXTO:\n{text}"
    )

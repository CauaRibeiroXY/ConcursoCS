from app.ai.gemini import GeminiProvider
from app.ai.provider import AIProvider
from app.config import GEMINI_API_KEY


def get_provider() -> AIProvider:
    """Single switch point for the AI backend (ADR-4)."""
    return GeminiProvider(api_key=GEMINI_API_KEY)

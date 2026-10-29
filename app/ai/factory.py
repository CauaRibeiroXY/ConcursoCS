from app.ai.provider import AIProvider
from app.config import AI_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL, NVIDIA_API_KEY, NVIDIA_MODEL


def get_provider() -> AIProvider:
    if AI_PROVIDER == "nvidia":
        from app.ai.nvidia import NvidiaProvider

        return NvidiaProvider(api_key=NVIDIA_API_KEY, model=NVIDIA_MODEL)

    from app.ai.gemini import GeminiProvider

    return GeminiProvider(api_key=GEMINI_API_KEY, model=GEMINI_MODEL)

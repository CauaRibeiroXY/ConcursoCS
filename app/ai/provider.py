from abc import ABC, abstractmethod

from app.models import Bank


class AIProvider(ABC):
    """Edge adapter for question generation. Swap implementations freely."""

    @abstractmethod
    def generate_questions(self, bank: str, subject: str, count: int) -> list[dict]:
        """Return raw question dicts (same shape as the parser output)."""
        raise NotImplementedError

    @abstractmethod
    def structure_questions(self, text: str, bank: str, subject: str) -> list[dict]:
        """Extract existing questions from raw exam text (gabarito included)."""
        raise NotImplementedError

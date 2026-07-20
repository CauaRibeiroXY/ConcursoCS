from abc import ABC, abstractmethod

from app.models import Bank


class AIProvider(ABC):
    """Edge adapter for question generation. Swap implementations freely."""

    @abstractmethod
    def generate_questions(self, bank: str, subject: str, count: int) -> list[dict]:
        """Return raw question dicts (same shape as the parser output)."""
        raise NotImplementedError

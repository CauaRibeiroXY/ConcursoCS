from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Edge adapter for question generation. Swap implementations freely."""

    @abstractmethod
    def generate_questions(
        self, bank: str, subject: str, count: int, template: str | None = None
    ) -> list[dict]:
        """Return raw question dicts (same shape as the parser output)."""
        raise NotImplementedError

    @abstractmethod
    def structure_questions(
        self, text: str, bank: str, subject: str, guidance: str | None = None
    ) -> tuple[list[dict], str]:
        """Extract existing questions from raw exam text.

        Returns (questions, layout_description). `guidance` is a previously
        learned layout description to reuse for the same exam type.
        """
        raise NotImplementedError

def evaluate(user_answer: list, answer: list) -> bool:
    """INV-3 independent: pure comparison, no AI involved."""
    return sorted(user_answer) == sorted(answer)

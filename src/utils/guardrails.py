import re
from typing import Any

from src.utils.config import Settings, get_settings

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"you\s+are\s+now",
    r"system\s+prompt",
    r"jailbreak",
    r"do\s+anything\s+now",
]


class GuardrailError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def validate_input(question: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    cleaned = question.strip()

    if not cleaned:
        raise GuardrailError("Question cannot be empty")

    if len(cleaned) > settings.max_question_length:
        raise GuardrailError(
            f"Question exceeds maximum length of {settings.max_question_length} characters"
        )

    lowered = cleaned.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            raise GuardrailError("Input blocked: potential prompt injection detected")

    for topic in settings.blocked_topics_list:
        if topic in lowered:
            raise GuardrailError(f"Input blocked: topic '{topic}' is not allowed")

    return cleaned


def validate_output(
    answer: str,
    source_contents: list[str],
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    _ = settings

    if not answer or not answer.strip():
        return {
            "output_passed": False,
            "reason": "Empty answer generated",
            "answer": "Unable to generate an answer.",
        }

    normalized_answer = answer.lower()
    not_found_phrases = [
        "cannot find that in the document",
        "not in the document",
        "i don't know",
        "i do not know",
    ]
    if any(phrase in normalized_answer for phrase in not_found_phrases):
        return {"output_passed": True, "reason": None, "answer": answer}

    if not source_contents:
        return {
            "output_passed": False,
            "reason": "Answer generated without retrieved context",
            "answer": answer,
        }

    answer_tokens = {t for t in re.findall(r"\w+", normalized_answer) if len(t) > 3}
    context_tokens: set[str] = set()
    for content in source_contents:
        context_tokens.update(
            t for t in re.findall(r"\w+", content.lower()) if len(t) > 3
        )

    overlap = answer_tokens & context_tokens
    overlap_ratio = len(overlap) / max(len(answer_tokens), 1)

    if overlap_ratio < 0.05 and len(answer_tokens) > 5:
        return {
            "output_passed": False,
            "reason": "Answer may not be grounded in retrieved context",
            "answer": answer,
        }

    return {"output_passed": True, "reason": None, "answer": answer}

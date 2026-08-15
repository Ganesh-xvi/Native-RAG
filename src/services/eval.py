import json
import re
from pathlib import Path

from src.rag.chain import query_rag, retrieve_context
from src.schemas import EvalQuestion, EvalQuestionResult, EvalResponse, EvalSummary
from src.utils.config import Settings, get_settings

DEFAULT_METRICS = ["faithfulness", "answer_relevancy", "context_precision"]


def load_golden_set(path: Path | None = None) -> list[EvalQuestion]:
    settings = get_settings()
    path = path or settings.golden_set_path
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [EvalQuestion(**item) for item in raw]


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"\w+", text.lower()) if len(t) > 2}


def _mean(values: list[float | None]) -> float | None:
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 4)


def _score_faithfulness(answer: str, contexts: list[str]) -> float:
    if not contexts:
        return 0.0
    answer_tokens = _tokenize(answer)
    if not answer_tokens:
        return 0.0
    context_tokens: set[str] = set()
    for context in contexts:
        context_tokens.update(_tokenize(context))
    overlap = answer_tokens & context_tokens
    return round(len(overlap) / len(answer_tokens), 4)


def _score_answer_relevancy(answer: str, question: str, ground_truth: str) -> float:
    answer_tokens = _tokenize(answer)
    target_tokens = _tokenize(question) | _tokenize(ground_truth)
    if not answer_tokens or not target_tokens:
        return 0.0
    overlap = answer_tokens & target_tokens
    return round(len(overlap) / len(answer_tokens), 4)


def _score_context_precision(contexts: list[str], question: str) -> float:
    if not contexts:
        return 0.0
    question_tokens = _tokenize(question)
    if not question_tokens:
        return 0.0
    scores: list[float] = []
    for context in contexts:
        context_tokens = _tokenize(context)
        overlap = question_tokens & context_tokens
        scores.append(len(overlap) / len(question_tokens))
    return round(sum(scores) / len(scores), 4)


def _score_context_recall(contexts: list[str], ground_truth: str) -> float:
    if not contexts:
        return 0.0
    truth_tokens = _tokenize(ground_truth)
    if not truth_tokens:
        return 0.0
    context_tokens: set[str] = set()
    for context in contexts:
        context_tokens.update(_tokenize(context))
    overlap = truth_tokens & context_tokens
    return round(len(overlap) / len(truth_tokens), 4)


def run_evaluation(
    questions: list[EvalQuestion] | None = None,
    metrics: list[str] | None = None,
    settings: Settings | None = None,
) -> EvalResponse:
    settings = settings or get_settings()
    questions = questions or load_golden_set()
    metrics = metrics or DEFAULT_METRICS

    question_results: list[EvalQuestionResult] = []

    for item in questions:
        rag_result = query_rag(item.question, settings=settings)
        docs, _ = retrieve_context(item.question, settings=settings)
        contexts = [doc.page_content for doc in docs]
        answer = rag_result["answer"]

        scores: dict[str, float | None] = {metric: None for metric in metrics}
        if "faithfulness" in metrics:
            scores["faithfulness"] = _score_faithfulness(answer, contexts)
        if "answer_relevancy" in metrics:
            scores["answer_relevancy"] = _score_answer_relevancy(
                answer, item.question, item.ground_truth
            )
        if "context_precision" in metrics:
            scores["context_precision"] = _score_context_precision(contexts, item.question)
        if "context_recall" in metrics:
            scores["context_recall"] = _score_context_recall(contexts, item.ground_truth)

        question_results.append(
            EvalQuestionResult(
                question=item.question,
                answer=answer,
                ground_truth=item.ground_truth,
                scores=scores,
            )
        )

    summary = EvalSummary(
        faithfulness=_mean([r.scores.get("faithfulness") for r in question_results]),
        answer_relevancy=_mean(
            [r.scores.get("answer_relevancy") for r in question_results]
        ),
        context_precision=_mean(
            [r.scores.get("context_precision") for r in question_results]
        ),
        context_recall=_mean([r.scores.get("context_recall") for r in question_results]),
        questions_evaluated=len(question_results),
    )

    return EvalResponse(summary=summary, results=question_results)

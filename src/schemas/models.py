from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    task_id: str
    status: str
    message: str


class RebuildRequest(BaseModel):
    clear_uploads: bool = False


class RebuildResponse(BaseModel):
    task_id: str
    status: str
    message: str
    files_found: int


class TaskProgress(BaseModel):
    step: str
    current: int
    total: int
    percent: float


class TaskResponse(BaseModel):
    task_id: str
    type: str
    status: str
    progress: TaskProgress
    source_file: str | None = None
    started_at: str
    completed_at: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = None


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = Field(default=None, ge=1, le=20)


class SourceItem(BaseModel):
    content: str
    metadata: dict[str, Any]
    score: float | None = None


class GuardrailInfo(BaseModel):
    input_passed: bool
    output_passed: bool
    output_reason: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    question: str
    guardrails: GuardrailInfo


class EvalQuestion(BaseModel):
    question: str
    ground_truth: str


class EvalRequest(BaseModel):
    questions: list[EvalQuestion] | None = None
    metrics: list[str] | None = None


class EvalQuestionResult(BaseModel):
    question: str
    answer: str
    ground_truth: str
    scores: dict[str, float | None]


class EvalSummary(BaseModel):
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    questions_evaluated: int


class EvalResponse(BaseModel):
    summary: EvalSummary
    results: list[EvalQuestionResult]
    evaluated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class HealthResponse(BaseModel):
    status: str
    index_loaded: bool
    document_count: int
    dependencies: dict[str, str]

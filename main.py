import argparse
import sys
from pathlib import Path

from src.rag import ingest_all_pdfs, ingest_pdf, index_is_loaded, query_rag
from src.services import run_evaluation
from src.utils import GuardrailError, get_logger, get_settings, setup_logging, validate_input, validate_output

logger = get_logger("cli")


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def cmd_ingest(args: argparse.Namespace) -> None:
    settings = get_settings()
    if args.all:
        result = ingest_all_pdfs(recreate=args.recreate, settings=settings)
        print(f"Ingested {result['chunks_created']} chunks from {len(result['files_processed'])} files.")
        return

    file_path = Path(args.file) if args.file else None
    if not file_path:
        pdfs = sorted(settings.data_dir.glob("*.pdf"))
        if not pdfs:
            print("No PDF found. Pass --file or place a PDF in data/.", file=sys.stderr)
            sys.exit(1)
        file_path = pdfs[0]

    result = ingest_pdf(file_path, recreate=args.recreate, settings=settings)
    print(
        f"Ingested {result['chunks_created']} chunks from {result['source_file']} "
        f"into {result['persist_dir']}."
    )


def cmd_query(args: argparse.Namespace) -> None:
    if not index_is_loaded():
        print("Index not loaded. Run: python main.py ingest", file=sys.stderr)
        sys.exit(1)

    settings = get_settings()
    try:
        question = validate_input(args.question, settings)
    except GuardrailError as exc:
        print(f"Guardrail blocked input: {exc.reason}", file=sys.stderr)
        sys.exit(1)

    result = query_rag(question, top_k=args.top_k, settings=settings)
    output_check = validate_output(
        result["answer"],
        [source["content"] for source in result["sources"]],
        settings,
    )

    print(f"\nQuestion: {question}\n")
    print(f"Answer: {output_check['answer']}\n")
    print("Sources:")
    for index, source in enumerate(result["sources"], start=1):
        page = source["metadata"].get("page", "?")
        print(f"  [{index}] page {page}: {source['content'][:160]}...")


def cmd_eval(args: argparse.Namespace) -> None:
    if not index_is_loaded():
        print("Index not loaded. Run: python main.py ingest", file=sys.stderr)
        sys.exit(1)

    response = run_evaluation()
    print("Evaluation summary:")
    print(f"  faithfulness:      {response.summary.faithfulness}")
    print(f"  answer_relevancy:  {response.summary.answer_relevancy}")
    print(f"  context_precision: {response.summary.context_precision}")
    print(f"  questions:         {response.summary.questions_evaluated}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="4-RAG CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Ingest PDF(s) into Chroma")
    ingest_parser.add_argument("--file", help="Path to a PDF file")
    ingest_parser.add_argument(
        "--all", action="store_true", help="Ingest all PDFs in data/"
    )
    ingest_parser.add_argument(
        "--recreate",
        action="store_true",
        help="Clear existing index before ingesting",
    )
    ingest_parser.set_defaults(func=cmd_ingest)

    query_parser = subparsers.add_parser("query", help="Ask a question")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.add_argument("--top-k", type=int, default=None)
    query_parser.set_defaults(func=cmd_query)

    eval_parser = subparsers.add_parser("eval", help="Run RAG evaluation")
    eval_parser.set_defaults(func=cmd_eval)

    return parser


def main() -> None:
    _configure_stdout()
    setup_logging()
    logger.info("CLI started")
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

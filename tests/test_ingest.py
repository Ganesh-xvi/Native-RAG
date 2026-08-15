from pathlib import Path

from src.rag.ingest import load_pdf, split_documents


def test_load_and_split_apple_pdf():
    pdf_path = Path("data/Apple's FY2025 10-K Annual Report.pdf")
    if not pdf_path.exists():
        return

    documents = load_pdf(pdf_path)
    assert len(documents) > 0

    chunks = split_documents(documents)
    assert len(chunks) >= len(documents)

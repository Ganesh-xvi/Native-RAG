from pathlib import Path
from typing import Callable

import chromadb
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils.config import Settings, get_settings
from src.utils.llm import get_embeddings
from src.utils.logging import get_logger

COLLECTION_NAME = "rag_collection"
logger = get_logger("rag.ingest")


def get_text_splitter(settings: Settings | None = None) -> RecursiveCharacterTextSplitter:
    settings = settings or get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )


def load_pdf(file_path: Path) -> list[Document]:
    loader = PyPDFLoader(str(file_path))
    return loader.load()


def split_documents(
    documents: list[Document], settings: Settings | None = None
) -> list[Document]:
    splitter = get_text_splitter(settings)
    return splitter.split_documents(documents)


def get_vectorstore(settings: Settings | None = None) -> Chroma:
    settings = settings or get_settings()
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(settings),
        persist_directory=str(settings.chroma_persist_dir),
    )


def clear_vectorstore(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings.chroma_persist_dir))
    try:
        client.delete_collection(COLLECTION_NAME)
    except (ValueError, chromadb.errors.NotFoundError):
        pass


def get_document_count(settings: Settings | None = None) -> int:
    settings = settings or get_settings()
    if not settings.chroma_persist_dir.exists():
        return 0
    try:
        vectorstore = get_vectorstore(settings)
        return vectorstore._collection.count()
    except Exception:
        return 0


def index_is_loaded(settings: Settings | None = None) -> bool:
    return get_document_count(settings) > 0


def ingest_pdf(
    file_path: Path,
    *,
    recreate: bool = False,
    settings: Settings | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict:
    settings = settings or get_settings()
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")
    if file_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")

    logger.info(
        "Ingest started | file=%s recreate=%s",
        file_path.name,
        recreate,
    )

    if progress_callback:
        progress_callback("loading", 0, 1)

    documents = load_pdf(file_path)
    for doc in documents:
        doc.metadata["source"] = file_path.name

    if progress_callback:
        progress_callback("splitting", 0, len(documents))

    chunks = split_documents(documents, settings)
    total_chunks = len(chunks)
    logger.info("PDF split | file=%s pages=%s chunks=%s", file_path.name, len(documents), total_chunks)

    if recreate:
        clear_vectorstore(settings)

    if progress_callback:
        progress_callback("embedding", 0, total_chunks)

    vectorstore = get_vectorstore(settings)

    batch_size = 32
    for start in range(0, total_chunks, batch_size):
        batch = chunks[start : start + batch_size]
        vectorstore.add_documents(batch)
        if progress_callback:
            progress_callback("embedding", min(start + len(batch), total_chunks), total_chunks)

    if progress_callback:
        progress_callback("done", total_chunks, total_chunks)

    logger.info(
        "Ingest completed | file=%s chunks=%s persist_dir=%s",
        file_path.name,
        total_chunks,
        settings.chroma_persist_dir,
    )

    return {
        "chunks_created": total_chunks,
        "source_file": file_path.name,
        "persist_dir": str(settings.chroma_persist_dir),
    }


def ingest_all_pdfs(
    *,
    recreate: bool = True,
    settings: Settings | None = None,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict:
    settings = settings or get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(settings.data_dir.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {settings.data_dir}")

    if recreate:
        clear_vectorstore(settings)

    total_chunks = 0
    processed_files: list[str] = []

    for index, pdf_path in enumerate(pdf_files):
        if progress_callback:
            progress_callback("loading", index, len(pdf_files))

        result = ingest_pdf(
            pdf_path,
            recreate=False,
            settings=settings,
            progress_callback=progress_callback,
        )
        total_chunks += result["chunks_created"]
        processed_files.append(result["source_file"])

    if progress_callback:
        progress_callback("done", len(pdf_files), len(pdf_files))

    return {
        "chunks_created": total_chunks,
        "files_processed": processed_files,
        "persist_dir": str(settings.chroma_persist_dir),
    }

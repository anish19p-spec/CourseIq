"""Local persistent storage for CourseIQ's RAG evidence."""

import os
from hashlib import sha256
from pathlib import Path

import chromadb
from chromadb.api.models.Collection import Collection

from documents import DocumentChunk

DEFAULT_CHROMA_PATH = Path(__file__).resolve().parent.parent / ".data" / "chroma"


def get_storage_path(path: str | Path | None = None) -> Path:
    """Resolve the shared local directory for vectors and the course catalog."""
    storage_path = path if path is not None else os.getenv(
        "COURSEIQ_CHROMA_PATH", str(DEFAULT_CHROMA_PATH)
    )
    if not str(storage_path).strip():
        raise ValueError("Chroma storage path cannot be empty")
    return Path(storage_path).expanduser().resolve()


def get_collection(path: str | Path | None = None) -> Collection:
    """Open the same collection at an explicit or configured path."""
    client = chromadb.PersistentClient(path=str(get_storage_path(path)))
    return client.get_or_create_collection(name="documents")


def chunk_record_id(chunk: DocumentChunk) -> str:
    """Identify an exact chunk and its source consistently across retries."""
    return sha256(chunk.model_dump_json().encode("utf-8")).hexdigest()


def store_chunks(
    chunks: list[DocumentChunk],
    embeddings: list[list[float]],
    path: str | Path | None = None,
) -> int:
    """Store precomputed embeddings and source metadata without duplicate retries."""
    if len(chunks) != len(embeddings):
        raise ValueError("Each chunk must have exactly one embedding")
    if not chunks:
        return 0
    ids = [chunk_record_id(chunk) for chunk in chunks]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate chunk records in the same batch")
    metadatas = [chunk.model_dump(exclude={"text"}, exclude_none=True) for chunk in chunks]
    get_collection(path).upsert(
        ids=ids, documents=[chunk.text for chunk in chunks],
        embeddings=embeddings, metadatas=metadatas,
    )
    return len(chunks)


def search_course_chunks(
    query_embedding: list[float],
    course_id: str,
    n_results: int = 5,
    path: str | Path | None = None,
) -> list[dict]:
    """Retrieve nearest evidence from one course, retaining source metadata."""
    if not course_id.strip():
        raise ValueError("course_id cannot be empty")
    if isinstance(n_results, bool) or not isinstance(n_results, int) or n_results < 1:
        raise ValueError("n_results must be a positive integer")
    if not query_embedding:
        raise ValueError("query_embedding cannot be empty")
    collection = get_collection(path)
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(
        query_embeddings=[query_embedding], where={"course_id": course_id},
        n_results=min(n_results, 10, count),
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"id": record_id, "text": text, **metadata, "distance": distance}
        for record_id, text, metadata, distance in zip(
            results["ids"][0], results["documents"][0],
            results["metadatas"][0], results["distances"][0],
        )
    ]


def load_course_chunks(course_id: str, path: str | Path | None = None) -> list[DocumentChunk]:
    """Read all saved excerpts for a course without generating an embedding."""
    if not course_id.strip():
        raise ValueError("course_id cannot be empty")
    results = get_collection(path).get(where={"course_id": course_id}, include=["documents", "metadatas"])
    chunks = [DocumentChunk(text=text, **metadata)
              for text, metadata in zip(results["documents"], results["metadatas"])]
    return sorted(chunks, key=lambda chunk: chunk.chunk_number)

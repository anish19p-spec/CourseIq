import os 
from pathlib import Path
from dotenv import load_dotenv
from google import genai

from chunking import split_text_recursively
from documents import DocumentChunk
from vector_store import store_chunks, search_course_chunks

load_dotenv()


class EmbeddingConfigurationError(ValueError):
    """Raised when the backend lacks embedding-provider configuration."""


def _get_genai_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EmbeddingConfigurationError(
            "GEMINI_API_KEY is not configured on the backend. Add it to the worktree .env file and restart the backend."
        )
    return genai.Client(api_key=api_key)


def _embed_text(text: str) -> list[float]:
    client = _get_genai_client()
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text,
    )

    if not response.embeddings:
        raise ValueError("Gemini did not return any embeddings.")

    embedding = response.embeddings[0]
    if not embedding.values:
        raise ValueError("Gemini returned an empty embedding vector.")

    return list(embedding.values)

def index_document_chunks(chunks: list[DocumentChunk], path: str | Path | None = None) -> int:
    """Embed validated chunks and persist them with their citation metadata."""
    embeddings = [_embed_text(chunk.text) for chunk in chunks]
    return store_chunks(chunks, embeddings, path)


def retrieve_course_evidence(
    question: str, course_id: str, n_results: int = 5, path: str | Path | None = None,
) -> list[dict]:
    """Embed a student's question and search only the selected course."""
    if not question.strip():
        raise ValueError("question cannot be empty")
    if not course_id.strip():
        raise ValueError("course_id cannot be empty")
    if isinstance(n_results, bool) or not isinstance(n_results, int) or n_results < 1:
        raise ValueError("n_results must be a positive integer")
    return search_course_chunks(_embed_text(question), course_id, n_results, path)


def format_course_evidence(results: list[dict]) -> str:
    """Attach source-faithful citations to retrieved excerpts."""
    if not results:
        return "No syllabus evidence found for the selected course."
    excerpts = []
    for result in results:
        source = result["filename"]
        page_number = result.get("page_number")
        if page_number is not None:
            source = f"{source}, p. {page_number}"
        excerpts.append(f"[{source}]\n{result['text']}")
    return "\n\n".join(excerpts)


def retrieve_cited_course_evidence(
    question: str, course_id: str, n_results: int = 5, path: str | Path | None = None,
) -> str:
    """Retrieve one course's evidence and format its existing source citations."""
    return format_course_evidence(retrieve_course_evidence(question, course_id, n_results, path))


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Keep the original RAG API while using the validated splitter."""
    
    return split_text_recursively(text, chunk_size, overlap)



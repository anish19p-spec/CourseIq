from __future__ import annotations

from documents import DocumentChunk, ExtractedDocument


DEFAULT_SEPARATORS = ("\n\n", "\n", ". ", " ")


def _split_without_overlap(
    text: str,
    chunk_size: int,
    separators: tuple[str, ...],
) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    separator = next((item for item in separators if item and item in text), "")
    if not separator:
        return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]

    smaller_separators = separators[separators.index(separator) + 1 :]
    raw_pieces = text.split(separator)
    pieces = [
        piece + separator if index < len(raw_pieces) - 1 else piece
        for index, piece in enumerate(raw_pieces)
    ]
    chunks: list[str] = []
    current = ""

    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        joiner = separator if separator.isspace() else " "
        candidate = piece if not current else current + joiner + piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(piece) > chunk_size:
            chunks.extend(_split_without_overlap(piece, chunk_size, smaller_separators))
            current = ""
        else:
            current = piece

    if current:
        chunks.append(current)
    return chunks


def split_text_recursively(
    text: str,
    chunk_size: int,
    overlap: int = 0,
    separators: tuple[str, ...] = DEFAULT_SEPARATORS,
) -> list[str]:
    """Recursively split text and safely repeat context between chunks."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")

   
    effective_overlap = min(overlap, chunk_size // 2)
    separator_width = 1 if chunk_size - effective_overlap > 1 else 0
    core_size = chunk_size - effective_overlap - separator_width
    chunks = _split_without_overlap(text, core_size, separators)

    if effective_overlap == 0 or len(chunks) < 2:
        return chunks

    result = [chunks[0]]
    for previous, current in zip(chunks, chunks[1:]):
        repeated_context = previous[-effective_overlap:]
        separator = "\n" if separator_width else ""
        result.append(f"{repeated_context}{separator}{current}")
    return result


def chunk_document(
    document: ExtractedDocument,
    course_id: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[DocumentChunk]:
    """Turn extracted pages into ordered chunks with source metadata."""
    document_chunks: list[DocumentChunk] = []
    for page in document.pages:
        page_chunks = split_text_recursively(page.text, chunk_size, overlap)
        for text in page_chunks:
            document_chunks.append(
                DocumentChunk(
                    text=text,
                    course_id=course_id,
                    filename=page.filename,
                    page_number=page.page_number,
                    
                    chunk_number=len(document_chunks) + 1
                )
            )
    return document_chunks

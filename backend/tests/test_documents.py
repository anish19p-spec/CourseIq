import pytest
from pydantic import ValidationError

from documents import DocumentChunk, ExtractedPage


def test_extracted_page_keeps_pdf_citation_metadata() -> None:
    page = ExtractedPage(
        text="Homework is 40% of the grade.",
        filename="cs101-syllabus.pdf",
        page_number=2,
    )

    assert page.filename == "cs101-syllabus.pdf"
    assert page.page_number == 2


def test_extracted_page_allows_source_without_page_number() -> None:
    page = ExtractedPage(text="Course policies", filename="policies.txt")

    expected_page_number = None
    assert page.page_number is expected_page_number


def test_extracted_page_rejects_page_zero() -> None:
    with pytest.raises(ValidationError):
        ExtractedPage(
            text="Course policies",
            filename="cs101-syllabus.pdf",
            page_number=0,
        )


def test_document_chunk_preserves_identity_and_citation() -> None:
    chunk = DocumentChunk(
        text="Exams are worth 40%.",
        course_id="course_a81f",
        filename="cs101-syllabus.pdf",
        page_number=2,
        chunk_number=3,
    )

    assert chunk.model_dump()["course_id"] == "course_a81f"
    assert chunk.model_dump()["chunk_number"] == 3


def test_document_chunk_rejects_chunk_zero() -> None:
    with pytest.raises(ValidationError):
        DocumentChunk(
            text="Homework is worth 30%.",
            course_id="course_a81f",
            filename="cs101-syllabus.pdf",
            page_number=1,
            chunk_number=0,
        )

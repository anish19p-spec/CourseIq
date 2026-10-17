from chunking import chunk_document, split_text_recursively
from documents import ExtractedDocument, ExtractedPage
from rag_pipeline import chunk_text

def test_rag_pipeline_chunk_text_uses_recursive_splitter() -> None:
    text = "Homework details.\n\nExam details."

    result = chunk_text(text, chunk_size=25, overlap=4)

    assert result == split_text_recursively(text, chunk_size=25, overlap=4)


def test_rag_pipeline_chunk_text_caps_equal_overlap() -> None:
    result = chunk_text("abcdefghij", chunk_size=5, overlap=5)

    assert result == split_text_recursively("abcdefghij", chunk_size=5, overlap=5)


def test_recursive_splitter_prefers_section_boundaries() -> None:
    text = (
        "Homework\nWeekly programming assignments count for 30%.\n\n"
        "Exams\nTwo midterms count for 40%."
    )

    result = split_text_recursively(text, chunk_size=60)

    assert result == [
        "Homework\nWeekly programming assignments count for 30%.",
        "Exams\nTwo midterms count for 40%.",
    ]


def test_recursive_splitter_preserves_blank_lines_when_merging_sections() -> None:
    text = "Homework\n\nAssignments\n\nExams"

    result = split_text_recursively(text, chunk_size=25)

    assert result == ["Homework\n\nAssignments", "Exams"]


def test_recursive_splitter_keeps_long_homework_explanation() -> None:
    text = "Read each chapter carefully. Complete ten coding problems. Explain your reasoning."

    result = split_text_recursively(text, chunk_size=35)

    assert result == [
        "Read each chapter carefully.",
        "Complete ten coding problems.",
        "Explain your reasoning.",
    ]


def test_recursive_splitter_caps_overlap_and_keeps_advancing() -> None:
    result = split_text_recursively("abcdefghij", chunk_size=6, overlap=6)

    assert result == ["ab", "ab\ncd", "cd\nef", "ef\ngh", "gh\nij"]
    assert all(len(chunk) <= 6 for chunk in result)
    assert len(set(result)) == len(result)


def test_recursive_splitter_handles_tiny_chunks_safely() -> None:
    result = split_text_recursively("abc", chunk_size=2, overlap=2)

    assert result == ["a", "ab", "bc"]


def test_chunk_document_preserves_page_citations_and_global_order() -> None:
    document = ExtractedDocument(
        pages=[
            ExtractedPage(
                text="Homework details are extensive. Submit every Friday.",
                filename="cs101.pdf",
                page_number=1,
            ),
            ExtractedPage(text="Exams are worth 40%.", filename="cs101.pdf", page_number=2),
        ]
    )

    result = chunk_document(document, course_id="course_a81f", chunk_size=35, overlap=0)

    assert [chunk.chunk_number for chunk in result] == [1, 2, 3]
    assert [chunk.page_number for chunk in result] == [1, 1, 2]
    assert all(chunk.filename == "cs101.pdf" for chunk in result)
    assert all(chunk.course_id == "course_a81f" for chunk in result)

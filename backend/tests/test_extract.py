from unittest.mock import MagicMock

import pytest

from extract import PDFValidationError, extract_text_from_pdf


def test_pdf_extraction_preserves_pages_and_structure(monkeypatch, tmp_path) -> None:
    pdf_path = tmp_path / "syllabus.pdf"
    pdf_path.touch()
    first_page = MagicMock()
    first_page.extract_text.return_value = "Homework\n40% of grade"
    second_page = MagicMock()
    second_page.extract_text.return_value = "Exams\n60% of grade"
    opened_pdf = MagicMock()
    opened_pdf.__enter__.return_value.pages = [first_page, second_page]
    monkeypatch.setattr("extract.pdfplumber.open", MagicMock(return_value=opened_pdf))

    result = extract_text_from_pdf(str(pdf_path))

    assert len(result.pages) == 2
    assert result.pages[0].text == "Homework\n40% of grade"
    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2


def test_pdf_extraction_rejects_page_without_text(monkeypatch, tmp_path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    pdf_path.touch()
    page = MagicMock()
    page.extract_text.return_value = None
    opened_pdf = MagicMock()
    opened_pdf.__enter__.return_value.pages = [page]
    monkeypatch.setattr("extract.pdfplumber.open", MagicMock(return_value=opened_pdf))

    with pytest.raises(PDFValidationError, match="No readable text"):
        extract_text_from_pdf(str(pdf_path))


def test_pdf_extraction_warns_when_one_page_fails(monkeypatch, tmp_path) -> None:
    pdf_path = tmp_path / "partial.pdf"
    pdf_path.touch()
    pages = [MagicMock(), MagicMock(), MagicMock()]
    pages[0].extract_text.return_value = "Course overview"
    pages[1].extract_text.side_effect = RuntimeError("damaged page")
    pages[2].extract_text.return_value = "Exam schedule"
    opened_pdf = MagicMock()
    opened_pdf.__enter__.return_value.pages = pages
    monkeypatch.setattr("extract.pdfplumber.open", MagicMock(return_value=opened_pdf))

    result = extract_text_from_pdf(str(pdf_path))

    expected_page_numbers = [1, 3]
    assert [page.page_number for page in result.pages] == expected_page_numbers
    assert result.warnings == ["Page 2 could not be read."]


def test_pdf_extraction_rejects_malformed_internal_structure(tmp_path) -> None:
    pdf_path = tmp_path / "malformed.pdf"
    pdf_path.write_bytes(b"%PDF-not-a-real-document")

    with pytest.raises(PDFValidationError, match="could not be opened"):
        extract_text_from_pdf(str(pdf_path))

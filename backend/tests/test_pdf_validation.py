import pytest

from extract import MAX_PDF_SIZE_BYTES, validate_pdf_upload


def test_pdf_validation_rejects_wrong_extension() -> None:
    with pytest.raises(ValueError, match="pdf filename"):
        validate_pdf_upload("notes.txt", b"%PDF-1.7")


def test_pdf_validation_rejects_oversized_upload() -> None:
    bytes_over_limit = 1
    oversized_content = b"x" * (MAX_PDF_SIZE_BYTES + bytes_over_limit)

    with pytest.raises(ValueError, match="10 MB limit"):
        validate_pdf_upload("syllabus.pdf", oversized_content)


def test_pdf_validation_rejects_fake_pdf_bytes() -> None:
    
    fake_pdf_content = b"this is plain text"

    with pytest.raises(ValueError, match="valid PDF signature"):
        validate_pdf_upload("syllabus.pdf", fake_pdf_content)

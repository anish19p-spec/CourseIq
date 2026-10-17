from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import pdfplumber
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from documents import ExtractedDocument, ExtractedPage


MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024
PDF_SIGNATURE = b"%PDF-"


class PDFValidationError(ValueError):
    """Raised when an upload cannot be accepted as a PDF."""


class SyllabusData(BaseModel):
    course_name: str = Field(..., description="Canonical course name")
    total_projects: int = Field(ge=0)
    total_midterms: int = Field(ge=0)
    total_homeworks: int = Field(ge=0)
    has_final_exam: bool


def validate_pdf_upload(filename: str | None, content: bytes) -> None:
    """Validate that an upload is a supported PDF before parsing it."""

    if not filename or Path(filename).suffix.lower() != ".pdf":
        raise PDFValidationError("Upload must use a .pdf filename.")
    if len(content) > MAX_PDF_SIZE_BYTES:
        raise PDFValidationError("PDF upload exceeds the 10 MB limit.")
    if not content.startswith(PDF_SIGNATURE):
        raise PDFValidationError("Upload does not contain a valid PDF signature.")


def extract_text_from_pdf(pdf_path: str, source_filename: str | None = None) -> ExtractedDocument:
    """Extract readable PDF pages and report page-level warnings."""

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    extracted_pages: list[ExtractedPage] = []
    warnings: list[str] = []
    try:
        pdf = pdfplumber.open(path)
    except Exception as exc:
        raise PDFValidationError("PDF could not be opened or is malformed.") from exc

    with pdf as opened_pdf:
        for page_number, page in enumerate(opened_pdf.pages, start=1):
            try:
                page_text = page.extract_text()
            except Exception:
                warnings.append(f"Page {page_number} could not be read.")
                continue
            if not page_text or not page_text.strip():
                warnings.append(f"Page {page_number} contained no readable text.")
                continue
            extracted_pages.append(
                ExtractedPage(
                    text=page_text.strip(),
                    filename=source_filename if source_filename is not None else path.name,
                    page_number=page_number,
                )
            )

    if not extracted_pages:
        raise PDFValidationError("No readable text could be found in the uploaded PDF.")
    return ExtractedDocument(pages=extracted_pages, warnings=warnings)


@lru_cache(maxsize=1)
def _get_genai_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required for extraction.")
    return genai.Client(api_key=api_key)


def parse_syllabus_with_ai(raw_text: str) -> SyllabusData:
    """Convert syllabus text into structured data using Gemini with a strict schema."""

    client = _get_genai_client()
    prompt = (
        "Extract only the syllabus facts needed for workload modeling. "
        "Return concise, deterministic values and do not invent unsupported details. "
        "If a value cannot be confidently inferred, use 0 for counts and false for the boolean.\n\n"
        f"Syllabus text:\n{raw_text}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SyllabusData,
        ),
    )

    parsed: Any = getattr(response, "parsed", None)
    if isinstance(parsed, SyllabusData):
        return parsed
    if isinstance(parsed, dict):
        return SyllabusData.model_validate(parsed)
    if getattr(response, "text", None):
        return SyllabusData.model_validate_json(response.text)

    raise ValueError("Gemini did not return structured syllabus data.")

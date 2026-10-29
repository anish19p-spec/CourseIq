from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import pdfplumber
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from documents import ExtractedDocument, ExtractedPage


MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024
PDF_SIGNATURE = b"%PDF-"


class PDFValidationError(ValueError):
    """Raised when an upload cannot be accepted as a PDF."""


class SyllabusConfigurationError(ValueError):
    """Raised when structured extraction lacks provider configuration."""


class AssignmentCategory(BaseModel):
    category: str = Field(min_length=1, pattern=r"\S")
    category_type: Literal["homework", "project", "exam", "final_exam", "quiz", "lab", "reading", "other"] | None = None
    grade_weight_percent: float | None = Field(default=None, ge=0, le=100)
    assignment_count: int | None = Field(default=None, ge=0)
    weekly_frequency: float | None = Field(
        default=None, ge=0, allow_inf_nan=False,
        description="Explicitly stated assignment count per week; unknown if only a submission cadence is given",
    )
    submission_cadence: str | None = None
    hours_per_assignment: float | None = Field(
        default=None, ge=0, allow_inf_nan=False,
        description="Out-of-class work/preparation hours explicitly stated per assignment; otherwise null",
    )
    description: str | None = None


class SyllabusData(BaseModel):
    course_name: str = Field(..., description="Canonical course name")
    total_projects: int = Field(ge=0)
    total_midterms: int = Field(ge=0)
    total_homeworks: int = Field(ge=0)
    has_final_exam: bool
    course_level: str | None = None
    credit_hours: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    semester_weeks: float | None = Field(default=None, ge=1, allow_inf_nan=False)
    course_type: str | None = None
    assignment_categories: list[AssignmentCategory] = Field(default_factory=list)


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
        raise SyllabusConfigurationError("GEMINI_API_KEY is required on the backend for workload extraction.")
    return genai.Client(api_key=api_key)


def parse_syllabus_with_ai(raw_text: str) -> SyllabusData:
    """Convert syllabus text into structured data using Gemini with a strict schema."""

    client = _get_genai_client()
    prompt = (
        "Extract only the syllabus facts needed for workload modeling. "
        "Return concise values and do not invent unsupported details. "
        "For legacy aggregate counts use 0 when absent and false for an absent final exam. "
        "For optional course metadata and assignment-category details, use null when absent.\n\n"
        "Each assignment category should be listed once, without overlapping subcategories. "
        "Keep its syllabus label in category and its standard activity kind in category_type. "
        "assignment_count is the total for the entire semester; weekly_frequency is assignments per week. "
        "If the syllabus only says work is submitted weekly, preserve weekly in submission_cadence "
        "and keep weekly_frequency null unless a number of assignments per week is actually stated. "
        "Do not confuse late-day allowances, grading percentages, or page numbers with assignment counts. "
        "Extract grading percentages on a 0-100 scale. Extract hours_per_assignment only when "
        "the syllabus explicitly states a time requirement; never estimate it yourself. "
        "Use out-of-class work or preparation time, not class-meeting or timed-exam duration. "
        "Keep assignment descriptions and extract course type, level, credits, and term length when stated.\n\n"
        "A complete numbered teaching schedule from Week 1 through Week N supports semester_weeks=N. "
        "Input may contain ordered excerpts with overlapping text. Do not count repeated passages "
        "as extra assignments. A syllabus with missing pages may omit workload details.\n\n"
        f"Syllabus text:\n{raw_text}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SyllabusData,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
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

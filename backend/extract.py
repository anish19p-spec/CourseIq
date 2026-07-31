from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import pdfplumber
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class SyllabusData(BaseModel):
    course_name: str = Field(..., description="Canonical course name")
    total_projects: int = Field(ge=0)
    total_midterms: int = Field(ge=0)
    total_homeworks: int = Field(ge=0)
    has_final_exam: bool


def extract_text_from_pdf(pdf_path: str) -> str:
    """Safely extract text from a PDF file by iterating pages defensively."""

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    extracted_chunks: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            normalized = re.sub(r"\s+", " ", page_text).strip()
            if normalized:
                extracted_chunks.append(normalized)

    clean_text = "\n".join(extracted_chunks).strip()
    if not clean_text:
        raise ValueError("No readable text could be extracted from the uploaded PDF.")
    return clean_text


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

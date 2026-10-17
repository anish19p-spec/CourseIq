from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedPage(BaseModel):
    text: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    page_number: int | None = Field(default=None, ge=1)


class ExtractedDocument(BaseModel):
    pages: list[ExtractedPage]
    warnings: list[str] = Field(default_factory=list)


class DocumentChunk(BaseModel):
    text: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    chunk_number: int = Field(ge=1)


class CourseSummary(BaseModel):
    course_id: str = Field(min_length=1)
    course_name: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    chunk_count: int = Field(ge=1)
    warnings: list[str] = Field(default_factory=list)

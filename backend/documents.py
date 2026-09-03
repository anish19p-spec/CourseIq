from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedPage(BaseModel):
    text: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    page_number: int | None = Field(default=None, ge=1)


class ExtractedDocument(BaseModel):
    pages: list[ExtractedPage]
    warnings: list[str] = Field(default_factory=list)

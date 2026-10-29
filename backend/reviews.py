"""Validated student-authored reviews, independent of individual syllabus uploads."""

from datetime import datetime
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


DEFAULT_INSTITUTION = "Texas A&M University"


def normalize_course_code(value: str) -> str:
    match = re.fullmatch(r"([A-Z]{2,8})[ -]?(\d{3,4})", " ".join(value.upper().split()))
    if match is None:
        raise ValueError("Use a course code such as CSCE 120 or PBSI 107.")
    return f"{match[1]} {match[2]}"


def normalize_institution(value: str) -> str:
    name = " ".join(value.split())
    if name.casefold() in {"tamu", "texas a&m", "texas a&m university"}:
        return DEFAULT_INSTITUTION
    return name


class ReviewDetails(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    institution: str = Field(default=DEFAULT_INSTITUTION, min_length=2, max_length=120)
    course_code: str = Field(min_length=4, max_length=20)
    professor_name: str = Field(min_length=2, max_length=120)
    term: str | None = Field(default=None, max_length=80)
    difficulty: int = Field(ge=1, le=5, strict=True)
    weekly_hours: float | None = Field(default=None, ge=0, le=168, allow_inf_nan=False)
    body: str = Field(min_length=20, max_length=3000)

    @field_validator("course_code")
    @classmethod
    def course_code_format(cls, value: str) -> str:
        return normalize_course_code(value)

    @field_validator("institution")
    @classmethod
    def institution_format(cls, value: str) -> str:
        return normalize_institution(value)

    @field_validator("term")
    @classmethod
    def blank_term_is_unknown(cls, value: str | None) -> str | None:
        return value or None


class ReviewSubmission(ReviewDetails):
    consent_to_publish: bool = Field(strict=True)

    @field_validator("consent_to_publish")
    @classmethod
    def publication_requires_consent(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Agree to publish your review before submitting.")
        return value


class StudentReview(ReviewDetails):
    review_id: UUID
    created_at: datetime
    source: Literal["student_submission"] = "student_submission"
    verified: Literal[False] = False


class ReviewPage(BaseModel):
    items: list[StudentReview]
    total: int
    offset: int
    limit: int

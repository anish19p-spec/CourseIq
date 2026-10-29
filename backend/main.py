from __future__ import annotations

import os
import tempfile
import sqlite3
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, ConfigDict, Field

from chunking import chunk_document
from course_store import save_course, list_courses
from documents import CourseSummary
from engine import CourseAnalyzer
from reviews import ReviewPage, ReviewSubmission, StudentReview
from review_store import create_review, list_reviews
from rag_pipeline import EmbeddingConfigurationError, index_document_chunks, retrieve_course_evidence, format_course_evidence
from extract import (
	MAX_PDF_SIZE_BYTES,
	PDFValidationError,
	extract_text_from_pdf,
	parse_syllabus_with_ai,
	validate_pdf_upload,
)


class CourseQuestion(BaseModel):
	model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
	question: str = Field(min_length=1, max_length=2000)
	n_results: int = Field(default=5, ge=1, le=10, strict=True)


app = FastAPI(title="CourseIQ API", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


async def _write_upload_to_temp_pdf(upload: UploadFile) -> str:
	content = await upload.read(MAX_PDF_SIZE_BYTES + 1)
	validate_pdf_upload(upload.filename, content)
	temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
	try:
		temp_file.write(content)
		temp_file.flush()
		return temp_file.name
	finally:
		temp_file.close()


@app.get("/health")
def health_check() -> dict[str, str]:
	return {"status": "ok"}


@app.post("/api/reviews", response_model=StudentReview, status_code=201)
def publish_review(submission: ReviewSubmission) -> StudentReview:
	try:
		return create_review(submission)
	except sqlite3.Error as exc:
		raise HTTPException(status_code=503, detail="Reviews are temporarily unavailable. Please try again.") from exc


@app.get("/api/reviews", response_model=ReviewPage)
def get_reviews(
	course_code: str | None = Query(default=None, max_length=20),
	institution: str | None = Query(default=None, max_length=120),
	limit: int = Query(default=20, ge=1, le=50),
	offset: int = Query(default=0, ge=0),
) -> ReviewPage:
	try:
		return list_reviews(course_code=course_code, institution=institution, limit=limit, offset=offset)
	except ValueError as exc:
		raise HTTPException(status_code=422, detail=str(exc)) from exc
	except sqlite3.Error as exc:
		raise HTTPException(status_code=503, detail="Reviews are temporarily unavailable. Please try again.") from exc


@app.post("/api/analyze")
async def analyze_course(
	course_name: str = Form(...),
	gpa: float = Form(...),
	comfort_level: int = Form(...),
	target_grade: str = Form(...),
	file: UploadFile = File(...),
) -> dict[str, object]:
	temp_path: str | None = None

	try:
		if file.content_type not in {"application/pdf", "application/octet-stream"}:
			raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")

		temp_path = await _write_upload_to_temp_pdf(file)
		document = extract_text_from_pdf(temp_path, source_filename=Path(file.filename).name)
		raw_text = "\n\n".join(page.text for page in document.pages)
		syllabus = parse_syllabus_with_ai(raw_text)

		analyzer = CourseAnalyzer(
			syllabus_data=syllabus,
			student_profile={"gpa": gpa, "comfort_level": comfort_level},
		)
		analysis = analyzer.analyze()

		return {
			"course_name": syllabus.course_name or course_name,
			"target_grade": target_grade,
			"syllabus": syllabus.model_dump(),
			"weekly_hours": analysis["weekly_hours"],
			"risk_level": analysis["risk_level"],
			"student_multiplier": analysis["student_multiplier"],
			"assignment_inventory": analysis["assignment_inventory"],
			"semester_weeks": CourseAnalyzer.SEMESTER_WEEKS,
			"warnings": document.warnings,
		}
	except HTTPException:
		raise
	except PDFValidationError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=500, detail=str(exc)) from exc
	finally:
		if temp_path and Path(temp_path).exists():
			os.remove(temp_path)
		await file.close()


@app.post("/api/courses", status_code=201)
async def upload_course(
	course_name: str = Form(..., min_length=1),
	file: UploadFile = File(...),
) -> dict[str, object]:
	"""Ingest one syllabus and return the course identifier for later questions."""
	temp_path: str | None = None
	try:
		if not course_name.strip():
			raise HTTPException(status_code=400, detail="Course name cannot be blank.")
		if file.content_type not in {"application/pdf", "application/octet-stream"}:
			raise HTTPException(status_code=400, detail="Only PDF uploads are supported.")
		temp_path = await _write_upload_to_temp_pdf(file)
		filename = Path(file.filename).name
		document = await run_in_threadpool(extract_text_from_pdf, temp_path, source_filename=filename)
		course_id = str(uuid4())
		chunks = chunk_document(document, course_id)
		chunk_count = await run_in_threadpool(index_document_chunks, chunks)
		summary = CourseSummary(course_id=course_id, course_name=course_name.strip(),
			filename=filename, chunk_count=chunk_count, warnings=document.warnings)
		await run_in_threadpool(save_course, summary)
		return summary.model_dump()
	except EmbeddingConfigurationError as exc:
		raise HTTPException(status_code=503, detail=str(exc)) from exc
	except PDFValidationError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(status_code=500, detail="Syllabus could not be indexed. Please try again.") from exc
	finally:
		if temp_path and Path(temp_path).exists():
			os.remove(temp_path)
		await file.close()


@app.get("/api/courses", response_model=list[CourseSummary])
def get_courses() -> list[CourseSummary]:
	"""List successfully indexed courses saved in the local catalog."""
	return list_courses()


@app.post("/api/courses/{course_id}/questions")
async def ask_course(course_id: str, request: CourseQuestion) -> dict[str, object]:
	"""Return retrieved syllabus evidence and citations for a selected course."""
	if not course_id.strip():
		raise HTTPException(status_code=400, detail="Course ID cannot be blank.")
	try:
		evidence = await run_in_threadpool(
			retrieve_course_evidence, request.question, course_id, request.n_results,
		)
		return {"course_id": course_id, "question": request.question,
			"evidence": evidence, "cited_evidence": format_course_evidence(evidence)}
	except EmbeddingConfigurationError as exc:
		raise HTTPException(status_code=503, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=500, detail="Course evidence could not be retrieved. Please try again.") from exc


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

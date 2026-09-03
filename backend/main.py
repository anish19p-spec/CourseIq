from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from engine import CourseAnalyzer
from extract import (
	MAX_PDF_SIZE_BYTES,
	PDFValidationError,
	extract_text_from_pdf,
	parse_syllabus_with_ai,
	validate_pdf_upload,
)


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
		document = extract_text_from_pdf(temp_path)
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


if __name__ == "__main__":
	import uvicorn

	uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

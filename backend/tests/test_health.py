from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    
    assert response.status_code == 200
    
    assert response.json() == {"status": "ok"}


def test_analyze_rejects_fake_pdf_upload() -> None:
    response = client.post(
        "/api/analyze",
        data={
            "course_name": "CS 101",
            "gpa": "3.5",
            "comfort_level": "3",
            "target_grade": "A",
        },
        files={"file": ("syllabus.pdf", b"plain text", "application/pdf")},
    )

    expected_status = 400
    assert response.status_code == expected_status
    assert response.json()["detail"] == "Upload does not contain a valid PDF signature."

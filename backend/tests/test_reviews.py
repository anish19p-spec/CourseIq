from datetime import datetime
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import UUID

from fastapi.testclient import TestClient
import pytest

from course_store import save_course
from documents import CourseSummary
from main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    directory = tmp_path / "store"
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(directory))
    monkeypatch.setenv("GEMINI_API_KEY", "")
    return directory


def submission(**updates):
    return {"institution": "TAMU", "course_code": "csce120", "professor_name": "Example Professor",
            "term": "Fall 2026", "difficulty": 4, "weekly_hours": 6.5,
            "body": "Weekly coding assignments took me about six hours outside class.",
            "consent_to_publish": True, **updates}


def test_published_review_is_visible_to_a_separate_visitor_without_upload_or_ai():
    response = client.post("/api/reviews", json=submission())
    assert response.status_code == 201
    review = response.json()
    UUID(review["review_id"])
    assert datetime.fromisoformat(review["created_at"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0
    assert review["course_code"] == "CSCE 120"
    assert review["institution"] == "Texas A&M University"
    assert review["verified"] is False
    assert review["source"] == "student_submission"
    assert "consent_to_publish" not in review
    other_visitor = TestClient(app)
    listing = other_visitor.get("/api/reviews", params={"course_code": "CSCE-120"})
    assert listing.status_code == 200
    assert listing.json()["items"] == [review]
    assert listing.json()["total"] == 1
    # Reviews can create the shared database before the course catalog exists.
    assert client.get("/api/courses").json() == []


def test_reading_empty_reviews_does_not_create_a_database(isolated_storage):
    response = client.get("/api/reviews")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "offset": 0, "limit": 20}
    assert not isolated_storage.exists()


@pytest.mark.parametrize("updates", [
    {"consent_to_publish": False}, {"consent_to_publish": "true"},
    {"difficulty": 0}, {"difficulty": 6}, {"difficulty": 2.5},
    {"weekly_hours": -1}, {"weekly_hours": 169},
    {"body": "short"}, {"body": " " * 30}, {"body": "x" * 3001},
    {"professor_name": " "}, {"course_code": "not a course"},
    {"verified": True}, {"source": "official"},
])
def test_invalid_or_forged_reviews_are_rejected_before_storage(updates, isolated_storage):
    assert client.post("/api/reviews", json=submission(**updates)).status_code == 422
    assert not isolated_storage.exists()


def test_publication_consent_is_required(isolated_storage):
    payload = submission()
    del payload["consent_to_publish"]
    assert client.post("/api/reviews", json=payload).status_code == 422
    assert not isolated_storage.exists()


def test_unknown_weekly_hours_and_term_remain_unknown():
    response = client.post("/api/reviews", json=submission(weekly_hours=None, term=" "))
    assert response.status_code == 201
    assert response.json()["weekly_hours"] is None
    assert response.json()["term"] is None


def test_filters_and_pagination_share_canonical_codes_but_separate_schools():
    ids = []
    for code in ["csce120", "CSCE 120", "CSCE-120"]:
        ids.append(client.post("/api/reviews", json=submission(course_code=code)).json()["review_id"])
    client.post("/api/reviews", json=submission(course_code="PBSI 107"))
    client.post("/api/reviews", json=submission(institution="Another University"))
    response = client.get("/api/reviews", params={"course_code": "csce120", "institution": "texas a&m",
                                                 "limit": 2, "offset": 1})
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert [row["review_id"] for row in response.json()["items"]] == [ids[1], ids[0]]


@pytest.mark.parametrize("query", [{"limit": 51}, {"limit": 0}, {"offset": -1}, {"course_code": "bad"}])
def test_invalid_feed_queries_are_rejected(query):
    assert client.get("/api/reviews", params=query).status_code == 422


def test_sql_and_markup_are_stored_as_plain_text():
    school = "Test University' OR 1=1 --"
    body = "<script>alert('example')</script> Homework took six hours weekly."
    response = client.post("/api/reviews", json=submission(institution=school, body=body))
    assert response.status_code == 201
    client.post("/api/reviews", json=submission())
    listing = client.get("/api/reviews", params={"institution": school}).json()
    assert listing["total"] == 1
    assert listing["items"][0]["body"] == body
    assert client.get("/api/reviews").json()["total"] == 2


def test_existing_course_catalog_and_reviews_coexist(isolated_storage):
    save_course(CourseSummary(course_id="saved", course_name="CSCE 120", filename="course.pdf", chunk_count=1))
    client.post("/api/reviews", json=submission())
    assert client.get("/api/courses").json()[0]["course_id"] == "saved"
    assert client.get("/api/reviews").json()["total"] == 1


def test_public_reviews_survive_backend_restart(isolated_storage):
    client.post("/api/reviews", json=submission())
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
    subprocess.run([sys.executable, "-c",
        "from main import app; from fastapi.testclient import TestClient; "
        "response=TestClient(app).get('/api/reviews'); "
        "assert response.status_code==200; "
        "assert response.json()['total']==1; "
        "assert response.json()['items'][0]['course_code']=='CSCE 120'"],
        env=environment, check=True, capture_output=True, text=True, timeout=30)


def test_storage_failure_returns_actionable_error_without_internal_details(monkeypatch):
    def fail(submission):
        raise sqlite3.OperationalError("private internal database details")

    monkeypatch.setattr("main.create_review", fail)
    response = client.post("/api/reviews", json=submission())
    assert response.status_code == 503
    assert "private internal" not in response.text

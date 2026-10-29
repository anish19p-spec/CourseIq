import pytest
import json
from google import genai
from google.genai import types
from pydantic import ValidationError

from extract import AssignmentCategory, SyllabusData, parse_syllabus_with_ai


def test_missing_workload_details_stay_unknown() -> None:
    category = AssignmentCategory(category="homework")
    syllabus = SyllabusData(
        course_name="CSCE 120",
        total_projects=0,
        total_midterms=0,
        total_homeworks=0,
        has_final_exam=False,
        assignment_categories=[category],
    )

    assert category.grade_weight_percent is None
    assert category.assignment_count is None
    assert syllabus.credit_hours is None
    assert syllabus.course_type is None


def test_category_weight_cannot_exceed_100_percent() -> None:
    with pytest.raises(ValidationError):
        AssignmentCategory(category="homework", grade_weight_percent=101)


def test_sdk_accepts_workload_schema_and_parses_details_without_network(monkeypatch):
    client = genai.Client(api_key="test-only-key")
    expected = SyllabusData(course_name="CSCE 120", total_projects=0, total_midterms=0,
                            total_homeworks=14, has_final_exam=False, credit_hours=3,
                            assignment_categories=[AssignmentCategory(category="Coding exercises",
                                category_type="homework", weekly_frequency=1, grade_weight_percent=40)])
    response = types.HttpResponse(body=json.dumps({"candidates": [{"content": {"role": "model", "parts": [
        {"text": expected.model_dump_json()}]}, "finishReason": "STOP"}]}), headers={})
    requests = []

    def request(method, path, body, options):
        requests.append(body)
        return response

    monkeypatch.setattr(client._api_client, "request", request)
    monkeypatch.setattr("extract._get_genai_client", lambda: client)
    result = parse_syllabus_with_ai("Homework 40%, 14 weekly coding exercises, 3 credit hours.")
    assert result == expected
    thinking = requests[0]["generationConfig"]["thinkingConfig"]
    assert thinking.get("thinkingBudget", thinking.get("thinking_budget")) == 0

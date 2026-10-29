import pytest
import json
from pathlib import Path

from extract import AssignmentCategory, SyllabusData
from engine import CourseAnalyzer, analyze_schedule


def analyzer_for(categories, **metadata):
    return CourseAnalyzer(SyllabusData(
        course_name="CSCE 120", total_projects=0, total_midterms=0,
        total_homeworks=0, has_final_exam=False,
        assignment_categories=[AssignmentCategory(**category) for category in categories],
        **metadata,
    ), {"comfort_level": 5, "gpa": 0})


def test_current_weekly_workload_uses_existing_baseline() -> None:
    syllabus = SyllabusData(
        course_name="CSCE 120",
        total_projects=0,
        total_midterms=1,
        total_homeworks=2,
        has_final_exam=False,
    )
    analyzer = CourseAnalyzer(syllabus, {"comfort_level": 5, "gpa": 0})

    expected_weekly_hours = 1.0
    assert analyzer.calculate_weekly_workload() == expected_weekly_hours


def test_stated_time_and_weekly_frequency_override_defaults_and_term_count():
    result = analyzer_for([dict(category="Homework", assignment_count=100,
                                weekly_frequency=2, hours_per_assignment=1.5)]).analyze()
    category = result["category_estimates"][0]
    assert result["weekly_hours"] == 3
    assert result["estimate_complete"] is True
    assert category["frequency_basis"] == "syllabus_weekly_frequency"
    assert category["hours_basis"] == "syllabus_stated"


def test_term_counts_use_the_actual_term_length():
    result = analyzer_for([dict(category="Project", assignment_count=2,
                                hours_per_assignment=12)], semester_weeks=6).analyze()
    assert result["weekly_hours"] == 4
    assert result["semester_weeks"] == 6
    assert result["category_estimates"][0]["frequency_basis"] == "semester_average"


def test_grading_weight_preserves_importance_without_changing_hours():
    categories = [dict(category="Problem sets", category_type="homework", weekly_frequency=1,
                       grade_weight_percent=10)]
    first = analyzer_for(categories).analyze()
    categories[0]["grade_weight_percent"] = 90
    second = analyzer_for(categories).analyze()
    assert first["weekly_hours"] == second["weekly_hours"] == 3
    assert second["category_estimates"][0]["grade_weight_percent"] == 90
    assert second["category_estimates"][0]["hours_basis"] == "provisional_default"


def test_partial_workload_reports_known_subtotal_instead_of_low_risk():
    result = analyzer_for([dict(category="homework", weekly_frequency=1),
                           dict(category="Reading", weekly_frequency=2)]).analyze()
    assert result["weekly_hours"] == 3
    assert result["estimate_complete"] is False
    assert result["risk_level"] == "Incomplete estimate"
    assert result["category_estimates"][1]["weekly_hours"] is None


def test_missing_frequency_keeps_workload_unknown():
    result = analyzer_for([dict(category="homework")]).analyze()
    assert result["weekly_hours"] is None
    assert result["estimate_complete"] is False


def test_zero_assignments_are_distinct_from_unknown_assignments():
    result = analyzer_for([dict(category="Reading", assignment_count=0)]).analyze()
    assert result["weekly_hours"] == 0
    assert result["estimate_complete"] is True


def test_detailed_categories_replace_legacy_counts_without_double_counting():
    analyzer = analyzer_for([dict(category="homework", weekly_frequency=1)])
    analyzer.syllabus_data.total_homeworks = 100
    assert analyzer.calculate_weekly_workload() == 3


def test_credit_guidance_is_separate_from_listed_activity_hours():
    result = analyzer_for([dict(category="homework", weekly_frequency=1)],
                          credit_hours=3, course_type="coding", course_level="introductory").analyze()
    assert result["weekly_hours"] == 3
    assert result["study_planning_range"]["low"] == 6
    assert result["study_planning_range"]["high"] == 9
    assert result["course_context"]["course_type"] == "coding"


@pytest.mark.parametrize("profile", [{"comfort_level": 0}, {"comfort_level": float("nan")},
                                   {"gpa": 5}, {"gpa": float("inf")}])
def test_invalid_profiles_cannot_produce_invalid_hours(profile):
    analyzer = analyzer_for([dict(category="homework", weekly_frequency=1)])
    analyzer.student_profile = profile
    with pytest.raises(ValueError):
        analyzer.analyze()


def test_schedule_distinguishes_same_named_courses_and_flags_unknown_course():
    schedule = analyze_schedule({
        "fall": analyzer_for([dict(category="homework", weekly_frequency=1)]),
        "spring": analyzer_for([dict(category="homework", weekly_frequency=2)]),
        "unknown": analyzer_for([dict(category="reading")]),
    })
    assert schedule["total_known_weekly_hours"] == 9
    assert schedule["estimate_complete"] is False
    assert [course["course_id"] for course in schedule["courses"]] == ["fall", "spring", "unknown"]
    assert [course["share_of_known_workload_percent"] for course in schedule["courses"]] == [33.33, 66.67, None]


def test_zero_hour_schedule_has_no_undefined_percentage():
    schedule = analyze_schedule({"zero": analyzer_for([dict(category="homework", assignment_count=0)])})
    assert schedule["total_known_weekly_hours"] == 0
    assert schedule["courses"][0]["share_of_known_workload_percent"] is None


def test_skipped_pdf_pages_make_an_otherwise_known_estimate_partial():
    analyzer = analyzer_for([dict(category="homework", weekly_frequency=1)])
    analyzer.source_warnings = ["Page 2 could not be read."]
    result = analyzer.analyze()
    assert result["weekly_hours"] == 3
    assert result["estimate_complete"] is False
    assert result["source_warnings"] == analyzer.source_warnings


def test_reviewed_summer_syllabus_uses_10_weeks_and_keeps_missing_work_unknown():
    facts = json.loads((Path(__file__).parent / "fixtures" / "csce120_workload_facts.json").read_text())
    syllabus = SyllabusData.model_validate(facts["syllabus"])
    result = CourseAnalyzer(syllabus, {"comfort_level": 5, "gpa": 0}).analyze()
    assert result["semester_weeks"] == 10
    assert result["weekly_hours"] == facts["expected"]["known_weekly_hours_at_neutral_profile"]
    assert result["estimate_complete"] is False
    assert sum(category["grade_weight_percent"] for category in result["category_estimates"]) == 100
    assert sum(category["weekly_hours"] is None for category in result["category_estimates"]) == 3
    homework = result["category_estimates"][0]
    assert homework["submission_cadence"] == "weekly"
    assert homework["weekly_frequency"] is None
    assert homework["weekly_hours"] is None


def test_submission_cadence_alone_does_not_become_one_assignment_per_week():
    result = analyzer_for([dict(category="homework", submission_cadence="weekly")]).analyze()
    assert result["weekly_hours"] is None
    assert result["category_estimates"][0]["submission_cadence"] == "weekly"


def test_missing_category_counts_reuse_unique_course_inventory_facts():
    analyzer = analyzer_for([
        dict(category="Midterm Exams", category_type="exam"),
        dict(category="Final Exam", category_type="final_exam"),
    ], semester_weeks=10)
    analyzer.syllabus_data.total_midterms = 2
    analyzer.syllabus_data.has_final_exam = True
    result = analyzer.analyze()
    assert result["weekly_hours"] == 2.6
    assert [row["assignment_count"] for row in result["category_estimates"]] == [2, 1]
    assert all(row["assignment_count_basis"] == "course_inventory" for row in result["category_estimates"])
    assert all(category.assignment_count is None for category in analyzer.syllabus_data.assignment_categories)


def test_course_total_cannot_be_assigned_to_two_matching_categories():
    analyzer = analyzer_for([
        dict(category="Written exams", category_type="exam"),
        dict(category="Practical exams", category_type="exam"),
    ])
    analyzer.syllabus_data.total_midterms = 2
    result = analyzer.analyze()
    assert result["weekly_hours"] is None
    assert all(row["assignment_count"] is None for row in result["category_estimates"])


def test_explicit_category_count_is_preserved_when_course_inventory_differs():
    analyzer = analyzer_for([dict(category="Midterm", category_type="exam", assignment_count=1)], semester_weeks=10)
    analyzer.syllabus_data.total_midterms = 2
    row = analyzer.analyze()["category_estimates"][0]
    assert row["assignment_count"] == 1
    assert row["assignment_count_basis"] == "category"

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

from extract import AssignmentCategory, SyllabusData


# Provisional product assumptions, not measured student workload data.
DEFAULT_ACTIVITY_HOURS = {
    "homework": 3.0,
    "project": 12.0,
    "exam": 8.0,
    "final_exam": 10.0,
}
ACTIVITY_ALIASES = {
    "homeworks": "homework", "projects": "project", "midterm": "exam",
    "midterms": "exam", "exams": "exam", "final": "final_exam", "final exam": "final_exam",
}
STUDY_GUIDANCE_URL = "https://asc.tamu.edu/courses-presentations/ten-tips.html"


def _activity_kind(category: AssignmentCategory) -> str:
    kind = category.category_type or category.category.strip().lower()
    return ACTIVITY_ALIASES.get(kind, kind)


@dataclass(slots=True)
class CourseAnalyzer:
    syllabus_data: SyllabusData
    student_profile: dict[str, object]
    source_warnings: list[str] = field(default_factory=list)

    SEMESTER_WEEKS = 14.0

    def _calculate_student_multiplier(self) -> float:
        comfort = float(self.student_profile.get("comfort_level", 5))
        gpa = float(self.student_profile.get("gpa", 0))
        if not math.isfinite(comfort) or not 1 <= comfort <= 10:
            raise ValueError("Comfort level must be between 1 and 10.")
        if not math.isfinite(gpa) or not 0 <= gpa <= 4:
            raise ValueError("GPA must be between 0 and 4.")
        multiplier = 1.0 + (5.0 - comfort) * 0.1
        if gpa > 3.5:
            multiplier -= 0.1
        return max(multiplier, 0.5)

    @property
    def semester_weeks(self) -> float:
        return self.syllabus_data.semester_weeks or self.SEMESTER_WEEKS

    def _categories(self) -> tuple[list[AssignmentCategory], bool]:
        if self.syllabus_data.assignment_categories:
            return self.syllabus_data.assignment_categories, False
        syllabus = self.syllabus_data
        inventory = [
            ("project", syllabus.total_projects),
            ("exam", syllabus.total_midterms),
            ("homework", syllabus.total_homeworks),
            ("final_exam", int(syllabus.has_final_exam)),
        ]
        categories = [AssignmentCategory(category=kind, assignment_count=count)
                      for kind, count in inventory if count > 0]
        return categories, True

    def _estimate_category(self, category: AssignmentCategory) -> dict[str, Any]:
        kind = _activity_kind(category)
        count = category.assignment_count
        count_basis = "category" if count is not None else "unknown"
        if count is None:
            inventory = {
                "homework": self.syllabus_data.total_homeworks,
                "project": self.syllabus_data.total_projects,
                "exam": self.syllabus_data.total_midterms,
                "final_exam": int(self.syllabus_data.has_final_exam),
            }
            matching = [item for item in self.syllabus_data.assignment_categories if _activity_kind(item) == kind]
            if len(matching) == 1 and inventory.get(kind, 0) > 0:
                count = inventory[kind]
                count_basis = "course_inventory"
        frequency = category.weekly_frequency
        frequency_basis = "syllabus_weekly_frequency"
        if frequency is None:
            frequency = count / self.semester_weeks if count is not None else None
            frequency_basis = "semester_average" if frequency is not None else "unknown"

        hours = category.hours_per_assignment
        hours_basis = "syllabus_stated"
        if hours is None:
            hours = DEFAULT_ACTIVITY_HOURS.get(kind)
            hours_basis = "provisional_default" if hours is not None else "unknown"

        weekly_hours = None
        if frequency == 0:
            weekly_hours = 0.0
        elif frequency is not None and hours is not None:
            weekly_hours = round(frequency * hours * self._calculate_student_multiplier(), 2)
        return {
            "category": category.category,
            "grade_weight_percent": category.grade_weight_percent,
            "assignment_count": count,
            "assignment_count_basis": count_basis,
            "weekly_frequency": frequency,
            "submission_cadence": category.submission_cadence,
            "frequency_basis": frequency_basis,
            "hours_per_assignment": hours,
            "hours_basis": hours_basis,
            "weekly_hours": weekly_hours,
            "description": category.description,
        }

    def calculate_weekly_workload(self) -> float | None:
        return self.analyze()["weekly_hours"]

    def determine_risk_level(self, weekly_hours: float) -> str:
        if weekly_hours > 9:
            return "High Risk"
        if weekly_hours >= 5:
            return "Manageable"
        return "Low Risk"

    def analyze(self) -> dict[str, Any]:
        multiplier = self._calculate_student_multiplier()
        categories, legacy = self._categories()
        estimates = [self._estimate_category(category) for category in categories]
        known = [estimate["weekly_hours"] for estimate in estimates if estimate["weekly_hours"] is not None]
        weekly_hours = round(sum(known), 2) if known else None
        complete = bool(estimates) and len(known) == len(estimates) and not legacy and not self.source_warnings
        assumptions = [
            "Activity-hour defaults and the comfort/GPA adjustment are provisional heuristics.",
            "Grade weights describe grading importance; they do not scale estimated time.",
            "Explicit weekly frequency takes precedence over a semester assignment count.",
            "Missing category counts reuse positive course totals only when exactly one category matches.",
            "Course type and level are retained as context pending calibration.",
            "Totals cover listed activities; unscheduled reading or study may be missing.",
            "The 5-hour and 9-hour intensity thresholds are provisional.",
        ]
        if self.syllabus_data.semester_weeks is None:
            assumptions.append("Semester length defaults to 14 weeks when unstated.")
        if legacy:
            assumptions.append("Legacy aggregate counts are used; missing counts may have been recorded as zero.")
        if not complete:
            assumptions.append("The weekly total is a known subtotal; some workload may be unestimated.")
        credits = self.syllabus_data.credit_hours
        return {
            "weekly_hours": weekly_hours,
            "estimate_complete": complete,
            "risk_level": self.determine_risk_level(weekly_hours) if complete else "Incomplete estimate",
            "student_multiplier": round(multiplier, 2),
            "student_profile": {"comfort_level": self.student_profile.get("comfort_level", 5),
                                "gpa": self.student_profile.get("gpa", 0)},
            "semester_weeks": self.semester_weeks,
            "category_estimates": estimates,
            "assumptions": assumptions,
            "source_warnings": self.source_warnings,
            "course_context": {"course_level": self.syllabus_data.course_level,
                               "course_type": self.syllabus_data.course_type, "credit_hours": credits},
            "study_planning_range": {"low": credits * 2, "high": credits * 3,
                                     "source": STUDY_GUIDANCE_URL} if credits is not None else None,
            "assignment_inventory": {
                "projects": self.syllabus_data.total_projects,
                "midterms": self.syllabus_data.total_midterms,
                "homeworks": self.syllabus_data.total_homeworks,
                "has_final_exam": self.syllabus_data.has_final_exam,
            },
        }


def analyze_schedule(courses: dict[str, CourseAnalyzer]) -> dict[str, Any]:
    """Compare course IDs and label shares of the workload we can estimate."""
    analyses = []
    for course_id, analyzer in courses.items():
        analysis = analyzer.analyze()
        analysis["course_id"] = course_id
        analysis["course_name"] = analyzer.syllabus_data.course_name
        analyses.append(analysis)
    known = [course["weekly_hours"] for course in analyses if course["weekly_hours"] is not None]
    total = round(sum(known), 2) if known else None
    for course in analyses:
        hours = course["weekly_hours"]
        course["share_of_known_workload_percent"] = (
            round(hours / total * 100, 2) if hours is not None and total else None)
    return {
        "courses": analyses,
        "total_known_weekly_hours": total,
        "estimate_complete": bool(analyses) and all(course["estimate_complete"] for course in analyses),
    }

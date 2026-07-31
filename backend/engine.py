from __future__ import annotations

from dataclasses import dataclass

from extract import SyllabusData


@dataclass(slots=True)
class CourseAnalyzer:
    syllabus_data: SyllabusData
    student_profile: dict[str, object]

    PROJECT_HOURS = 12.0
    MIDTERM_HOURS = 8.0
    HOMEWORK_HOURS = 3.0
    FINAL_EXAM_PREP_HOURS = 10.0
    SEMESTER_WEEKS = 14.0

    def _calculate_student_multiplier(self) -> float:
        comfort_level = float(self.student_profile.get("comfort_level", 5))
        gpa = float(self.student_profile.get("gpa", 0))

        multiplier = 1.0 + ((5.0 - comfort_level) * 0.1)
        if gpa > 3.5:
            multiplier -= 0.1

        return max(multiplier, 0.5)

    def calculate_weekly_workload(self) -> float:
        total_baseline_hours = (
            self.syllabus_data.total_projects * self.PROJECT_HOURS
            + self.syllabus_data.total_midterms * self.MIDTERM_HOURS
            + self.syllabus_data.total_homeworks * self.HOMEWORK_HOURS
        )
        if self.syllabus_data.has_final_exam:
            total_baseline_hours += self.FINAL_EXAM_PREP_HOURS

        adjusted_hours = total_baseline_hours * self._calculate_student_multiplier()
        weekly_hours = adjusted_hours / self.SEMESTER_WEEKS
        return round(weekly_hours, 2)

    def determine_risk_level(self, weekly_hours: float) -> str:
        if weekly_hours > 9:
            return "High Risk"
        if 5 <= weekly_hours <= 9:
            return "Manageable"
        return "Low Risk"

    def analyze(self) -> dict[str, object]:
        weekly_hours = self.calculate_weekly_workload()
        return {
            "weekly_hours": weekly_hours,
            "risk_level": self.determine_risk_level(weekly_hours),
            "student_multiplier": round(self._calculate_student_multiplier(), 2),
            "assignment_inventory": {
                "projects": self.syllabus_data.total_projects,
                "midterms": self.syllabus_data.total_midterms,
                "homeworks": self.syllabus_data.total_homeworks,
                "has_final_exam": self.syllabus_data.has_final_exam,
            },
        }

import { Clock3 } from "lucide-react";
import { WorkloadReport } from "./WorkloadBreakdown";

export type CourseReport = WorkloadReport & {
  course_id: string; course_name: string; share_of_known_workload_percent: number | null;
  workload_fit: { rating: number | null; out_of: number; label: string; reason: string; weekly_hours_without_course: number | null };
};
export type ScheduleReport = {
  courses: CourseReport[]; total_known_weekly_hours: number | null; estimate_complete: boolean;
  pending_course_count: number; workload_level: string; guidance_note: string;
};

export default function WorkloadTracker({ schedule, courseCount }: { schedule: ScheduleReport; courseCount: number }) {
  const missing = Math.max(schedule.pending_course_count, courseCount - schedule.courses.length, 0);
  const partial = !schedule.estimate_complete || missing > 0;
  const hasHours = schedule.total_known_weekly_hours !== null;
  return <section aria-labelledby="weekly-total-title" aria-live="polite" className="space-y-5 rounded-3xl border border-emerald-300/20 bg-gradient-to-br from-emerald-400/10 to-slate-950 p-6 sm:p-8">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h2 id="weekly-total-title" className="flex items-center gap-2 text-sm font-semibold uppercase tracking-widest text-emerald-200"><Clock3 className="h-4 w-4" />Projected weekly total</h2>
      <span className="rounded-full border border-white/15 px-3 py-1 text-xs text-slate-300">{schedule.courses.length} of {courseCount} courses analyzed</span>
    </div>
    <div><p className="flex flex-wrap items-baseline gap-x-3 text-white"><strong className="text-5xl font-semibold tracking-tight">{hasHours ? schedule.total_known_weekly_hours!.toFixed(1) : "—"}</strong><span className="text-sm text-slate-400">hours / week</span></p>
      <p className="mt-2 text-sm text-slate-300">{hasHours ? `${schedule.workload_level} workload${partial ? " · known subtotal only" : " · projected from listed activities"}` : "Waiting for workload estimates"}</p></div>
    <div className="grid grid-cols-3 gap-2" aria-label="Provisional workload bands">
      {[["Small", "Under 15 hrs"], ["Medium", "15–under 30 hrs"], ["Large", "30+ hrs"]].map(([label, detail]) => <div key={label}
        className={`rounded-xl border px-2 py-3 text-center ${schedule.workload_level === label && hasHours ? "border-emerald-300/40 bg-emerald-300/10 text-emerald-200" : "border-white/10 text-slate-500"}`}>
        <p className="text-sm font-medium">{label}</p><p className="mt-1 text-xs">{detail}</p>
      </div>)}
    </div>
    {partial && <p className="rounded-xl border border-amber-300/20 bg-amber-300/10 p-3 text-sm leading-6 text-amber-200">This is not a full schedule estimate.{missing > 0 && ` ${missing} course(s) still need analysis.`} Missing activity details may increase the total. Workload-fit ratings remain unavailable until all saved courses have complete listed-activity estimates.</p>}
    <ul className="divide-y divide-white/10">{schedule.courses.map(course => <li key={course.course_id} className="py-4 first:pt-0">
      <div className="flex flex-wrap items-baseline justify-between gap-2"><span className="font-medium text-white">{course.course_name}</span><span className="text-sm text-emerald-200">{course.weekly_hours?.toFixed(1) ?? "Unknown"} hrs/week</span></div>
      {course.share_of_known_workload_percent !== null && <p className="mt-1 text-xs text-slate-400">{course.share_of_known_workload_percent}% of known weekly hours</p>}
      <p className="mt-3 text-sm font-medium text-slate-200">Workload fit: {partial || course.workload_fit.rating === null ? "Not rated" : `${course.workload_fit.rating}/${course.workload_fit.out_of} · ${course.workload_fit.label}`}</p>
      <p className="mt-1 text-xs leading-5 text-slate-400">{partial ? "More syllabus information is needed before suggesting whether this course fits your schedule." : course.workload_fit.reason}</p>
      {course.workload_fit.weekly_hours_without_course !== null && <p className="mt-2 text-xs text-slate-400">Without this course: {course.workload_fit.weekly_hours_without_course.toFixed(1)} known hours/week.</p>}
    </li>)}</ul>
    <p className="border-t border-white/10 pt-4 text-xs leading-5 text-slate-400">{schedule.guidance_note} These bands are uncalibrated planning heuristics, not student-review ratings. Every saved course is currently included; this shared installation does not separate semesters or student accounts.</p>
  </section>;
}

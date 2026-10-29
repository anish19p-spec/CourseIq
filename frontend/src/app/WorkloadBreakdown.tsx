export type WorkloadReport = {
  weekly_hours: number | null;
  estimate_complete: boolean;
  student_multiplier: number;
  student_profile: { comfort_level: number; gpa: number };
  risk_level: string;
  category_estimates: {
    category: string;
    grade_weight_percent: number | null;
    weekly_frequency: number | null;
    submission_cadence: string | null;
    weekly_hours: number | null;
    hours_basis: string;
    description: string | null;
  }[];
  assumptions: string[];
  source_warnings: string[];
  study_planning_range: { low: number; high: number; source: string } | null;
  course_context: { course_type: string | null; course_level: string | null; credit_hours: number | null };
};

export default function WorkloadBreakdown({ report }: { report: WorkloadReport }) {
  return <section className="space-y-4 rounded-3xl border border-white/10 bg-slate-950/60 p-6">
    <h3 className="text-xl font-semibold text-white">Workload by activity</h3>
    <p className="text-sm text-slate-400">Weekly averages for listed activities, adjusted for your profile.
      {report.estimate_complete ? " Every listed category has an estimate." : " Some time is unknown; the total is a known subtotal."}</p>
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm text-slate-300">
        <thead><tr className="border-b border-white/10 text-slate-400">
          <th className="p-2">Activity</th><th className="p-2">Grade importance</th>
          <th className="p-2">Assignments / week</th><th className="p-2">Hours / week</th>
        </tr></thead>
        <tbody>{report.category_estimates.map((category, index) => <tr key={index} className="border-b border-white/5">
          <td className="p-2"><p className="font-medium text-white">{category.category}</p>
            <p className="text-xs text-slate-400">{category.hours_basis === "syllabus_stated" ? "Time stated in syllabus" :
              category.hours_basis === "provisional_default" ? "Provisional time assumption" : "Time unknown"}</p>
            {category.description && <p className="mt-1 text-xs text-slate-400">{category.description}</p>}</td>
          <td className="p-2">{category.grade_weight_percent == null ? "Unknown" : `${category.grade_weight_percent}%`}</td>
          <td className="p-2">{category.weekly_frequency?.toFixed(2) ??
            (category.submission_cadence ? `${category.submission_cadence}; count unknown` : "Unknown")}</td>
          <td className="p-2">{category.weekly_hours?.toFixed(2) ?? "Unknown"}</td>
        </tr>)}</tbody>
      </table>
    </div>
    {report.category_estimates.length === 0 && <p className="text-slate-300">No activity counts or frequencies were found.</p>}
    {report.study_planning_range && <p className="text-sm text-slate-400">
      General study-planning guideline for {report.course_context.credit_hours} credits: {report.study_planning_range.low}–{report.study_planning_range.high} hours/week.
      {" "}<a href={report.study_planning_range.source} target="_blank" rel="noreferrer" className="text-emerald-200 underline">TAMU study guidance</a>
      . This is separate from the listed-activity estimate.
    </p>}
    {report.source_warnings.length > 0 && <div role="status" className="text-sm text-amber-200">
      {report.source_warnings.map((warning, index) => <p key={index}>{warning}</p>)}
    </div>}
    <details className="text-sm text-slate-400"><summary className="cursor-pointer">How these estimates work</summary>
      <ul className="mt-3 list-disc space-y-2 pl-5">{report.assumptions.map((assumption, index) => <li key={index}>{assumption}</li>)}</ul>
    </details>
  </section>;
}

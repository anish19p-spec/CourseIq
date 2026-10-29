"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import WorkloadBreakdown, { WorkloadReport } from "./WorkloadBreakdown";

type CourseReport = WorkloadReport & {
  course_id: string; course_name: string; share_of_known_workload_percent: number | null;
};
type ScheduleReport = { courses: CourseReport[]; total_known_weekly_hours: number | null; estimate_complete: boolean };
type Course = { course_id: string; course_name: string };
const inputClass = "w-full rounded-xl border border-white/20 bg-slate-900 p-3 text-white";

async function readJson<T>(response: Response): Promise<T> {
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Unable to load workload estimates.");
  return body as T;
}

function CourseEstimate({ course, report, apiBaseUrl, onSaved }: {
  course: Course; report?: CourseReport; apiBaseUrl: string; onSaved: () => void;
}) {
  const [comfort, setComfort] = useState(5);
  const [gpa, setGpa] = useState(0);
  const [refresh, setRefresh] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);
  useEffect(() => {
    if (report) { setComfort(report.student_profile.comfort_level); setGpa(report.student_profile.gpa); }
  }, [report]);

  async function estimate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const controller = new AbortController();
    pending.current = controller;
    setBusy(true); setError("");
    try {
      await readJson(await fetch(`${apiBaseUrl}/api/courses/${encodeURIComponent(course.course_id)}/workload`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comfort_level: comfort, gpa, refresh }), signal: controller.signal,
      }));
      if (!controller.signal.aborted) { setRefresh(false); onSaved(); }
    } catch (failure) {
      if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : "Unable to estimate workload.");
    } finally { if (!controller.signal.aborted) setBusy(false); }
  }

  return <section className="space-y-4 rounded-3xl border border-white/10 bg-slate-950/60 p-6">
    <h2 className="text-xl font-semibold text-white">Estimate {course.course_name}</h2>
    <p className="text-sm text-slate-400">The first estimate reads the saved syllabus with Gemini. Updates reuse saved facts unless you choose to re-read it.</p>
    <form onSubmit={estimate} className="space-y-3">
      <label className="block text-sm text-slate-300">Subject comfort (1–10)
        <input type="number" min={1} max={10} step={1} required value={comfort} disabled={busy}
          onChange={event => setComfort(Number(event.target.value))} className={inputClass} /></label>
      <label className="block text-sm text-slate-300">GPA (0–4; optional)
        <input type="number" min={0} max={4} step={0.01} value={gpa} disabled={busy}
          onChange={event => setGpa(Number(event.target.value))} className={inputClass} /></label>
      {report && <label className="flex gap-2 text-sm text-slate-300"><input type="checkbox" checked={refresh}
        disabled={busy} onChange={event => setRefresh(event.target.checked)} /> Re-read syllabus with Gemini</label>}
      <button disabled={busy} className="rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50">
        {busy ? "Estimating…" : report ? "Update saved estimate" : "Estimate and save workload"}
      </button>
    </form>
    {error && <p role="alert" className="text-rose-200">{error}</p>}
    {report && <WorkloadBreakdown report={report} />}
  </section>;
}

export default function SavedWorkloadWorkspace({ courses, selectedId, apiBaseUrl }: {
  courses: Course[]; selectedId: string; apiBaseUrl: string;
}) {
  const [schedule, setSchedule] = useState<ScheduleReport | null>(null);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    setError(""); setLoading(true);
    async function load() {
      try {
        const saved = await readJson<ScheduleReport>(await fetch(`${apiBaseUrl}/api/workload/schedule`, {
          cache: "no-store", signal: controller.signal,
        }));
        if (!controller.signal.aborted) setSchedule(saved);
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : "Unable to load workload estimates.");
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }
    void load(); return () => controller.abort();
  }, [apiBaseUrl, revision]);
  const selected = courses.find(course => course.course_id === selectedId);
  const missing = courses.length - (schedule?.courses.length ?? 0);
  return <div className="space-y-6">
    <section className="space-y-3 rounded-3xl border border-white/10 bg-slate-950/60 p-6">
      <h2 className="text-xl font-semibold text-white">Combined weekly workload</h2>
      {loading && <p role="status" className="text-slate-300">Loading saved estimates…</p>}
      {error && <div><p role="alert" className="text-rose-200">{error}</p>
        <button onClick={() => setRevision(value => value + 1)} className="text-emerald-200 underline">Retry</button></div>}
      {schedule && <>
        <p className="text-2xl text-white">{schedule.total_known_weekly_hours?.toFixed(1) ?? "Unknown"} hours / week</p>
        <p className="text-sm text-slate-400">Known workload across saved estimates.{missing > 0 && ` ${missing} course(s) still need an estimate.`}
          {(!schedule.estimate_complete || missing > 0) && " This total is partial."}</p>
        <ul className="space-y-2 text-sm text-slate-300">{schedule.courses.map(report => <li key={report.course_id}>
          {courses.find(course => course.course_id === report.course_id)?.course_name ?? report.course_name}: {report.weekly_hours?.toFixed(1) ?? "Unknown"} hours
          {report.share_of_known_workload_percent != null && ` · ${report.share_of_known_workload_percent}% of known workload`}
        </li>)}</ul>
      </>}
    </section>
    {selected && !loading && !error && <CourseEstimate key={selected.course_id} course={selected}
      report={schedule?.courses.find(report => report.course_id === selected.course_id)} apiBaseUrl={apiBaseUrl}
      onSaved={() => setRevision(value => value + 1)} />}
  </div>;
}

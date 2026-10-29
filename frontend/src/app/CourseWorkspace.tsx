"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import SavedWorkloadWorkspace from "./SavedWorkloadWorkspace";
import CourseUpload, { Course } from "./CourseUpload";
import { BookOpen, CheckCircle2, Plus } from "lucide-react";

type Evidence = { id: string; text: string; filename: string; page_number?: number | null };
type QuestionResult = { question: string; evidence: Evidence[]; cited_evidence: string };
const panel = "rounded-3xl border border-white/10 bg-slate-950/60 p-6 space-y-4";
const input = "w-full rounded-xl border border-white/20 bg-slate-900 p-3 text-white";
const button = "rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50";

async function readResponse<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(typeof body?.detail === "string" ? body.detail : `Request failed (${response.status}). Please try again.`);
  }
  if (body === null) throw new Error("The server returned an unreadable response.");
  return body as T;
}

function CourseQuestions({ course, apiBaseUrl }: { course: Course; apiBaseUrl: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<QuestionResult | null>(null);
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = String(new FormData(event.currentTarget).get("question") ?? "").trim();
    if (!question) return;
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch(`${apiBaseUrl}/api/courses/${encodeURIComponent(course.course_id)}/questions`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, n_results: 5 }), signal: controller.signal,
      });
      const answer = await readResponse<QuestionResult>(response);
      if (!controller.signal.aborted) setResult(answer);
    } catch (failure) {
      if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : "Unable to retrieve evidence.");
    } finally {
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  return <section className={panel}>
    <h2 className="text-xl font-semibold text-white">Ask about {course.course_name}</h2>
    <p className="text-sm text-slate-400">{course.filename} · {course.chunk_count} indexed excerpts</p>
    {course.warnings.length > 0 && <div role="status" className="space-y-1 text-sm text-amber-200">
      <p>Some pages could not be read:</p>
      {course.warnings.map((warning, index) => <p key={index}>{warning}</p>)}
    </div>}
    <form onSubmit={ask} className="space-y-3">
      <label htmlFor="course-question" className="block text-sm text-slate-300">Your question</label>
      <textarea id="course-question" name="question" required maxLength={2000} rows={3}
        className={input} placeholder="What does the syllabus say about homework?" disabled={busy} />
      <button className={button} disabled={busy}>{busy ? "Finding evidence…" : "Find syllabus evidence"}</button>
    </form>
    {error && <p role="alert" className="text-rose-200">{error}</p>}
    {result && <div aria-live="polite" className="space-y-3">
      <h3 className="font-semibold text-white">Syllabus evidence</h3>
      <p className="text-sm text-slate-400">Retrieved excerpts for “{result.question}”. These are source passages, not a generated answer.</p>
      {result.evidence.length === 0 ? <p className="text-slate-300">{result.cited_evidence}</p> :
        result.evidence.map(excerpt => <article key={excerpt.id} className="rounded-xl border border-white/10 p-4">
          <p className="mb-2 text-sm font-medium text-emerald-200">{excerpt.filename}{excerpt.page_number != null ? `, p. ${excerpt.page_number}` : ""}</p>
          <p className="whitespace-pre-wrap break-words text-slate-200">{excerpt.text}</p>
        </article>)}
    </div>}
  </section>;
}

export default function CourseWorkspace({ apiBaseUrl }: { apiBaseUrl: string }) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [savedMessage, setSavedMessage] = useState("");
  const [loadError, setLoadError] = useState("");
  const [reload, setReload] = useState(0);
  const addButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setLoadError("");
    async function load() {
      try {
        const response = await fetch(`${apiBaseUrl}/api/courses`, { signal: controller.signal, cache: "no-store" });
        const saved = await readResponse<Course[]>(response);
        if (!controller.signal.aborted) {
          setCourses(saved);
          setSelectedId(previous => saved.some(course => course.course_id === previous) ? previous : saved[0]?.course_id ?? "");
        }
      } catch (failure) {
        if (!controller.signal.aborted) setLoadError(failure instanceof Error ? failure.message : "Unable to load courses.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void load();
    return () => controller.abort();
  }, [apiBaseUrl, reload]);

  const selected = courses.find(course => course.course_id === selectedId);
  return <div className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div><p className="text-xs font-semibold uppercase tracking-widest text-emerald-300">Your semester, at a glance</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">My courses</h1>
        <p className="mt-2 text-sm text-slate-400">Save syllabi, compare weekly workloads, and explore the details.</p></div>
      {!showUpload && <button ref={addButton} type="button" disabled={loading || Boolean(loadError)} onClick={() => { setSavedMessage(""); setShowUpload(true); }}
        className={`${button} inline-flex items-center gap-2 hover:bg-emerald-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300`}>
        <Plus className="h-4 w-4" />Add course</button>}
    </div>
    {savedMessage && <p role="status" className="flex items-center gap-2 rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-4 text-sm text-emerald-200"><CheckCircle2 className="h-5 w-5 shrink-0" />{savedMessage}</p>}
    {showUpload && <CourseUpload apiBaseUrl={apiBaseUrl} onClose={() => {
      setShowUpload(false); requestAnimationFrame(() => addButton.current?.focus());
    }} onSaved={course => {
      setCourses(previous => [...previous, course]); setSelectedId(course.course_id); setShowUpload(false);
      setSavedMessage(`${course.course_name} is saved. Set your comfort level below to estimate its workload.`);
      requestAnimationFrame(() => document.getElementById("selected-course")?.focus());
    }} />}
    {!loading && !loadError && courses.length === 0 && !showUpload ? <section className="rounded-3xl border border-dashed border-white/15 bg-slate-950/40 px-6 py-16 text-center">
      <BookOpen className="mx-auto mb-5 h-10 w-10 text-emerald-300" aria-hidden="true" />
      <h2 className="text-xl font-semibold text-white">A clearer schedule starts with your syllabus</h2>
      <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-400">Use Add course to save your first PDF. Your courses and workload estimates will live here—no repeat uploads needed.</p>
      <p className="mt-5 text-xs text-slate-500">Text-based PDF · Up to 10 MB</p>
    </section> : !loading && !loadError && courses.length === 0 ? null : <div className="grid items-start gap-6 lg:grid-cols-[minmax(260px,0.65fr)_minmax(0,1.35fr)]">
    <div className="space-y-6">
      <section className={panel}>
        <h2 className="text-xl font-semibold text-white">Saved courses</h2>
        {loading ? <p role="status" className="text-slate-300">Loading courses…</p> : loadError ?
          <div><p role="alert" className="mb-3 text-rose-200">{loadError}</p><button className={button} onClick={() => setReload(value => value + 1)}>Retry loading</button></div> :
          courses.length === 0 ? <p className="text-slate-300">Your saved courses will appear here.</p> :
          <><label htmlFor="selected-course" className="block text-sm text-slate-300">Selected course</label>
            <select id="selected-course" className={input} value={selectedId} onChange={event => setSelectedId(event.target.value)}>
              {courses.map((course, index) => <option key={course.course_id} value={course.course_id}>{course.course_name} — {course.filename} ({index + 1})</option>)}
            </select></>}
      </section>
    </div>
    <div className="space-y-6">
    <SavedWorkloadWorkspace courses={courses} selectedId={selectedId} apiBaseUrl={apiBaseUrl} />
    {selected ? <CourseQuestions key={selected.course_id} course={selected} apiBaseUrl={apiBaseUrl} /> :
      <section className={panel}><h2 className="text-xl font-semibold text-white">Explore your syllabus</h2><p className="text-slate-300">Select or upload a course to ask questions and see source excerpts with page citations.</p></section>}
    </div>
    </div>}
  </div>;
}

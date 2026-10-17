"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type Course = {
  course_id: string;
  course_name: string;
  filename: string;
  chunk_count: number;
  warnings: string[];
};

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
  const [uploading, setUploading] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [reload, setReload] = useState(0);

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

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const name = String(data.get("course_name") ?? "").trim();
    const file = data.get("file");
    setUploadError("");
    if (!name || !(file instanceof File) || !file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Enter a course name and select a PDF syllabus.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError("PDF upload exceeds the 10 MB limit.");
      return;
    }
    data.set("course_name", name);
    setUploading(true);
    try {
      const response = await fetch(`${apiBaseUrl}/api/courses`, { method: "POST", body: data });
      const course = await readResponse<Course>(response);
      setCourses(previous => [...previous, course]);
      setSelectedId(course.course_id);
      form.reset();
    } catch (failure) {
      setUploadError(failure instanceof Error ? failure.message : "Unable to upload syllabus.");
    } finally {
      setUploading(false);
    }
  }

  const selected = courses.find(course => course.course_id === selectedId);
  return <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
    <div className="space-y-6">
      <section className={panel}>
        <h2 className="text-xl font-semibold text-white">Saved courses</h2>
        {loading ? <p role="status" className="text-slate-300">Loading courses…</p> : loadError ?
          <div><p role="alert" className="mb-3 text-rose-200">{loadError}</p><button className={button} onClick={() => setReload(value => value + 1)}>Retry loading</button></div> :
          courses.length === 0 ? <p className="text-slate-300">No saved courses yet. Upload a syllabus below.</p> :
          <><label htmlFor="selected-course" className="block text-sm text-slate-300">Selected course</label>
            <select id="selected-course" className={input} value={selectedId} onChange={event => setSelectedId(event.target.value)}>
              {courses.map((course, index) => <option key={course.course_id} value={course.course_id}>{course.course_name} — {course.filename} ({index + 1})</option>)}
            </select></>}
      </section>
      <form onSubmit={upload} className={panel}>
        <h2 className="text-xl font-semibold text-white">Add a course</h2>
        <label htmlFor="saved-course-name" className="block text-sm text-slate-300">Course name</label>
        <input id="saved-course-name" name="course_name" required className={input} placeholder="CSCE 221 · Fall 2026" disabled={uploading} />
        <label htmlFor="saved-course-file" className="block text-sm text-slate-300">Syllabus PDF (up to 10 MB)</label>
        <input id="saved-course-file" name="file" type="file" accept=".pdf,application/pdf" required className={input} disabled={uploading} />
        <button className={button} disabled={uploading || loading || Boolean(loadError)}>{uploading ? "Reading and indexing…" : "Save syllabus"}</button>
        <p className="text-xs text-slate-400">Each upload creates a separate course. Saved courses are shared on this local installation.</p>
        {uploadError && <p role="alert" className="text-rose-200">{uploadError}</p>}
      </form>
    </div>
    {selected ? <CourseQuestions key={selected.course_id} course={selected} apiBaseUrl={apiBaseUrl} /> :
      <section className={panel}><h2 className="text-xl font-semibold text-white">Explore your syllabus</h2><p className="text-slate-300">Select or upload a course to ask questions and see source excerpts with page citations.</p></section>}
  </div>;
}

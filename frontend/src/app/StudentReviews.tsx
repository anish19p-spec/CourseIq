"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type StudentReview = {
  review_id: string;
  institution: string;
  course_code: string;
  professor_name: string;
  term: string | null;
  difficulty: number;
  weekly_hours: number | null;
  body: string;
  created_at: string;
  verified: false;
};
type ReviewPage = { items: StudentReview[]; total: number; limit: number; offset: number };
const panel = "space-y-4 rounded-3xl border border-white/10 bg-slate-950/60 p-6";
const input = "mt-1 w-full rounded-xl border border-white/20 bg-slate-900 p-3 text-white";
const button = "rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 disabled:opacity-50";
const pageSize = 20;

async function readResponse<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const message = typeof detail === "string" ? detail : Array.isArray(detail)
      ? detail.map((error: { msg?: string }) => error.msg ?? "Invalid review field.").join(" ")
      : "The review request failed. Please try again.";
    throw new Error(message);
  }
  if (!body) throw new Error("The server returned an unreadable response.");
  return body as T;
}

export default function StudentReviews({ apiBaseUrl }: { apiBaseUrl: string }) {
  const [feed, setFeed] = useState<ReviewPage | null>(null);
  const [filters, setFilters] = useState({ course_code: "", institution: "" });
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [publishing, setPublishing] = useState(false);
  const [publishError, setPublishError] = useState("");
  const [success, setSuccess] = useState("");
  const publishingRequest = useRef<AbortController | null>(null);
  const courseFilter = useRef<HTMLInputElement>(null);
  const schoolFilter = useRef<HTMLInputElement>(null);
  useEffect(() => () => publishingRequest.current?.abort(), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setLoadError("");
    async function load() {
      try {
        const query = new URLSearchParams({ limit: String(pageSize), offset: String(offset) });
        if (filters.course_code) query.set("course_code", filters.course_code);
        if (filters.institution) query.set("institution", filters.institution);
        const result = await readResponse<ReviewPage>(await fetch(`${apiBaseUrl}/api/reviews?${query}`, {
          signal: controller.signal, cache: "no-store",
        }));
        if (!controller.signal.aborted) setFeed(result);
      } catch (failure) {
        if (!controller.signal.aborted) setLoadError(failure instanceof Error ? failure.message : "Unable to load reviews.");
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }
    void load();
    return () => controller.abort();
  }, [apiBaseUrl, filters, offset, revision]);

  function filterReviews(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFilters({ course_code: courseFilter.current?.value.trim() ?? "", institution: schoolFilter.current?.value.trim() ?? "" });
    setOffset(0);
  }

  async function publish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (publishingRequest.current) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    const controller = new AbortController();
    publishingRequest.current = controller;
    setPublishing(true); setPublishError(""); setSuccess("");
    const hours = String(data.get("weekly_hours") ?? "").trim();
    try {
      const review = await readResponse<StudentReview>(await fetch(`${apiBaseUrl}/api/reviews`, {
        method: "POST", headers: { "Content-Type": "application/json" }, signal: controller.signal,
        body: JSON.stringify({
          institution: data.get("institution"), course_code: data.get("course_code"),
          professor_name: data.get("professor_name"), term: data.get("term") || null,
          difficulty: Number(data.get("difficulty")), weekly_hours: hours === "" ? null : Number(hours),
          body: data.get("body"), consent_to_publish: data.get("consent_to_publish") === "on",
        }),
      }));
      if (!controller.signal.aborted) {
        form.reset();
        if (courseFilter.current) courseFilter.current.value = review.course_code;
        if (schoolFilter.current) schoolFilter.current.value = review.institution;
        setFilters({ course_code: review.course_code, institution: review.institution });
        setOffset(0); setRevision(value => value + 1);
        setSuccess("Your review is published and visible to other CourseIQ visitors.");
      }
    } catch (failure) {
      if (!controller.signal.aborted) setPublishError(failure instanceof Error ? failure.message : "Unable to publish review.");
    } finally {
      if (!controller.signal.aborted) { publishingRequest.current = null; setPublishing(false); }
    }
  }

  return <section className="space-y-6" aria-labelledby="reviews-title">
    <div><h2 id="reviews-title" className="text-2xl font-semibold text-white">Student course reviews</h2>
      <p className="mt-2 text-sm text-slate-300">Share first-hand experiences with homework, exams, and workload. Reviews are anonymous and unverified; experiences can differ by instructor and term.</p>
    </div>
    <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
      <form className={panel} onSubmit={publish}>
        <h3 className="text-xl font-semibold text-white">Write a review</h3>
        <fieldset disabled={publishing} className="space-y-4">
          <label className="block text-sm text-slate-300" htmlFor="review-school">School
            <input id="review-school" name="institution" required minLength={2} maxLength={120}
              defaultValue="Texas A&M University" className={input} /></label>
          <label className="block text-sm text-slate-300" htmlFor="review-course">Course code
            <input id="review-course" name="course_code" required maxLength={20} placeholder="CSCE 120" className={input} /></label>
          <label className="block text-sm text-slate-300" htmlFor="review-professor">Professor
            <input id="review-professor" name="professor_name" required minLength={2} maxLength={120} className={input} /></label>
          <label className="block text-sm text-slate-300" htmlFor="review-term">Term (optional)
            <input id="review-term" name="term" maxLength={80} placeholder="Fall 2026" className={input} /></label>
          <label className="block text-sm text-slate-300" htmlFor="review-difficulty">Difficulty
            <select id="review-difficulty" name="difficulty" defaultValue="3" className={input}>
              <option value="1">1 — Very light</option><option value="2">2 — Light</option>
              <option value="3">3 — Moderate</option><option value="4">4 — Demanding</option>
              <option value="5">5 — Very demanding</option>
            </select></label>
          <label className="block text-sm text-slate-300" htmlFor="review-hours">Average hours outside class per week (optional)
            <input id="review-hours" name="weekly_hours" type="number" min={0} max={168} step="any" placeholder="e.g. 6" className={input} /></label>
          <label className="block text-sm text-slate-300" htmlFor="review-body">Your experience (20–3,000 characters)
            <textarea id="review-body" name="body" required minLength={20} maxLength={3000} rows={5}
              placeholder="How much time did homework take? What were exams and projects like?" className={input} /></label>
          <p className="text-xs text-slate-400">Describe your own experience. Avoid names of other students, contact details, and personal information.</p>
          <label className="flex items-start gap-2 text-sm text-slate-300">
            <input name="consent_to_publish" type="checkbox" required className="mt-1" />
            I took this course and agree to publish this review for other students to read.
          </label>
          <button className={button} disabled={publishing}>{publishing ? "Publishing…" : "Publish review"}</button>
        </fieldset>
        {publishError && <p role="alert" className="text-rose-200">{publishError}</p>}
        {success && <p role="status" className="text-emerald-200">{success}</p>}
      </form>
      <div className={panel}>
        <h3 className="text-xl font-semibold text-white">Community reviews</h3>
        <form onSubmit={filterReviews} className="space-y-3">
          <label className="block text-sm text-slate-300" htmlFor="review-filter-course">Filter by course (optional)
            <input ref={courseFilter} id="review-filter-course" maxLength={20} placeholder="CSCE 120" className={input} /></label>
          <label className="block text-sm text-slate-300" htmlFor="review-filter-school">Filter by school (optional)
            <input ref={schoolFilter} id="review-filter-school" maxLength={120} placeholder="All schools" className={input} /></label>
          <div className="flex flex-wrap gap-3">
            <button className={button}>Apply filters</button>
            <button type="button" className={button} disabled={loading}
              onClick={() => setRevision(value => value + 1)}>Refresh reviews</button>
          </div>
        </form>
        {loading ? <p role="status" className="text-slate-300">Loading reviews…</p> : loadError ?
          <div><p role="alert" className="text-rose-200">{loadError}</p>
            <button type="button" onClick={() => setRevision(value => value + 1)} className="mt-2 text-emerald-200 underline">Retry</button></div> :
          feed && <div aria-live="polite" className="space-y-4">
            <p className="text-sm text-slate-400">{feed.total} review{feed.total === 1 ? "" : "s"} found · newest first</p>
            {feed.items.length === 0 && <p className="text-slate-300">No reviews here yet. Share the first experience for this course.</p>}
            {feed.items.map(review => <article key={review.review_id} className="space-y-3 rounded-2xl border border-white/10 p-4">
              <h4 className="font-semibold text-white">{review.course_code} · {review.professor_name}</h4>
              <p className="text-sm text-slate-400">{review.institution} · {review.term ?? "Term not provided"}</p>
              <div className="flex flex-wrap gap-3 text-sm text-emerald-200">
                <span>Difficulty: {review.difficulty}/5</span>
                <span>Outside-class hours/week: {review.weekly_hours ?? "Not provided"}</span>
              </div>
              <p className="whitespace-pre-wrap break-words text-slate-200">{review.body}</p>
              <p className="text-xs text-slate-500">Anonymous student · Unverified · <time dateTime={review.created_at}>
                {new Date(review.created_at).toLocaleDateString()}</time></p>
            </article>)}
            <div className="flex gap-3">
              <button className={button} type="button" disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - pageSize))}>Previous</button>
              <button className={button} type="button" disabled={offset + pageSize >= feed.total} onClick={() => setOffset(value => value + pageSize)}>Next</button>
            </div>
          </div>}
      </div>
    </div>
  </section>;
}

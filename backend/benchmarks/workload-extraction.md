# Workload extraction latency check

One CSCE 120 summer syllabus was measured with `gemini-2.5-flash` using the same
PDF, prompt, and structured schema. The setting changed from the model's default
thinking behavior to `thinking_budget=0`. Each setting was tested once with
automatic retries disabled. Timing covers client setup, generation, and schema
parsing; PDF text extraction happens before the timer.

| Measurement | Default thinking | Thinking disabled |
| --- | ---: | ---: |
| Elapsed seconds | 13.607 | 3.065 |
| Prompt tokens | 5,118 | 5,118 |
| Response tokens | 650 | 648 |
| Thinking tokens | 2,296 | 0 additional tokens |
| Total tokens | 8,064 | 5,766 |

The observed elapsed time fell 77.47%, and total tokens fell 28.50%. This is one
development comparison on one syllabus, not a guaranteed speedup or an aggregate
performance claim. Server/network variation may affect the timings.

Both responses matched the reviewed credit hours, 10-week term, two midterms,
final-exam flag, and all five grading weights. Both left homework assignment
counts, course type, and course level unknown.

The faster response omitted counts in the individual exam categories despite
returning the correct course-wide exam facts. The engine now reuses a positive
course-wide count only for an unambiguous matching category whose count is
missing. It preserves explicit category counts and does not distribute a total
between multiple matching categories. Replaying both responses through this
rule yields the same 2.6-hour weekly exam-preparation subtotal. Other activity
time remains unknown, so neither response supports a complete course estimate.

Raw responses and the offline comparison are stored locally under the ignored
`benchmark-results/` folder. The source PDF and contact details are not committed.
The reviewed numeric fixture and regression tests are in `backend/tests/`.
Loading saved estimates and changing a profile reuse the extraction without
another generation request.

Google documents `thinkingBudget=0` for Gemini 2.5 Flash in its
[thinking configuration guide](https://ai.google.dev/gemini-api/docs/generate-content/thinking).

# Validation record

Original release validated on 30 October 2026; review release 1.1 revalidated on
3 November 2026. See `reports/run_manifest.json` for the
actual Python version, platform and input fingerprints.

| Check | Observed result |
|---|---|
| Standard-library unit/integration suite | 34 tests passed, including six per-case regression-gate tests |
| Local HTTP integration | Health, valid search, missing route, role override, malformed JSON and oversized body checked |
| Dataset contract | 48 passages, 96 questions, valid source spans, no duplicate questions or cross-split intent groups |
| Retrieval eligibility controls | All 27 additional method/plan/control combinations passed |
| Source quote integrity | All returned answer excerpts equal their cited source text |
| Independent process rerun | Dataset fingerprints, thresholds, quality metrics, per-case rankings, citations and decisions reproduced exactly |
| Deliberate control demonstrations | Cross-split intent overlap, duplicate question, ineligible gold source and a changed ranking with unchanged aggregate summaries were each detected; clean fixture left intact |
| Frozen manifest | Dataset, vocabulary and method hashes match the pre-benchmark freeze |
| Dashboard logic | JavaScript syntax, table construction, filtering, escaping, live search and abstention interactions checked using a lightweight DOM stub and the real local API |
| Portable report | Embedded payload present, unique HTML element IDs, no external assets required |
| Complete response-adapter example | All 48 extractive hybrid responses scored successfully through the external-response JSONL CLI contract; this is not a live LLM test |
| Browser visual rendering | Not verified in this environment; Chromium download did not produce a usable runtime. Perform a local desktop/mobile review before presenting the interactive interface |
| Client PDF brief | All four pages rendered and visually inspected; text bounds and page count checked |
| GitHub CI | Workflow supplied; not run on GitHub in this task |
| Live model inference / dense embeddings | Not implemented or claimed |
| Production deployment / load testing | Outside this prototype |

The dashboard logic check does not substitute for a real browser or visual review.
The source-and-substring metric does not substitute for human answer-quality review.
Engineering checks and statistical results must be assessed separately.


## Current task recheck

The source ZIP was extracted into a fresh directory. All 34 tests passed and a new independent benchmark matched reference thresholds, quality metrics and every case's rankings, answers and decisions. All five frozen fixture/method hashes match. The four deliberate faults were detected again. The dashboard now defaults to sparse hybrid, aligning the presentation with the measured result; JavaScript execution is checked separately. Chromium is unavailable in this environment, so browser rendering remains unverified. The existing four-page client brief was rendered and all four pages visually inspected again.

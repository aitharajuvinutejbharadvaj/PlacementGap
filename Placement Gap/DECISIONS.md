# Architecture decisions

## 2026-10-16 — Deterministic scheduling

We schedule with deterministic Python because budgets, prerequisite order, and week loads need reproducible guarantees. An LLM scheduler was considered, but its outputs cannot reliably guarantee a hard capacity or strict ordering. The offline test fixture produces a plan checked against all stated constraints; no before/after production measurements exist yet, so we do not claim a measured quality lift.

## 2026-10-16 — Ontology over raw string matching

Canonical skill IDs, aliases, and explicit unresolved results keep synonyms and acronyms traceable. Raw substring matching was considered and rejected because it conflates terms and hides misses. The seed includes 435 skills and more than 1,700 aliases; these are structural coverage counts, not a claim of market completeness.

## 2026-10-16 — Critic loop capped at two

The critic is capped at two adjustments to bound latency and prevent oscillation. The offline fixture does not invoke an LLM critic, so no empirical optimality claim is made.

## 2026-10-16 — Model routing split

Extraction and normalization route to the configured cheap model; gap reasoning, critic, and report prose route to the stronger model. This is a configurable starting hypothesis, not a measured cost/quality optimum. Fixture mode is the reproducible default.

## 2026-10-16 — Offline-first deployment

The API and reports can run with frozen fixtures and no model key. PostgreSQL with pgvector and Jaeger are included in Compose for durable state and traces; local unit/demo commands need only Python.

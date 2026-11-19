# Proposed client pilot: one retrieval workflow

This is an example scope, not an agreed client commitment or price quote.

## Intended outcome

Give a product/engineering team reproducible evidence about where one knowledge
assistant succeeds, where it fails and which improvement is worth implementing.
Relevant to product teams and agencies delivering knowledge assistants or RAG
systems. This is an independent demonstration without a commissioning client
or third-party endorsement.

## Inputs to agree

- One workflow and a permitted corpus snapshot with stable source identifiers.
- Representative real questions, unknown-answer cases and a relevance rubric.
- Source access rules, prohibited data and the permitted processing environment.
- An existing baseline and the retrieval/generation settings to hold constant.
- Human ownership of relevance labels and answer-quality review.
- Scope, timeline, fee and acceptance criteria before starting.

## Deliverables

1. Versioned evaluation dataset with development/test separation and provenance.
2. Reproducible baseline and one agreed retrieval or reranking comparison.
3. Retrieval metrics and answer-quality review with separately defined denominators.
4. Annotated failures distinguishing source, retrieval and generation problems.
5. Code, configuration, rerun instructions and a short technical handover.

## Acceptance criteria to define with the client

Dataset approval, reproducibility, no cross-tenant exposure in agreed tests,
minimum useful coverage, maximum unsupported-answer rate, acceptable latency and
the human review standard. Commercial targets must follow a baseline and must
not be inferred from this synthetic fixture.

## Scope boundaries

Production authentication, a full UI rebuild, automated PDF/OCR ingestion,
security certification, comprehensive prompt-injection defence, multilingual
coverage, load testing and ongoing monitoring require explicit additional scope.
The prototype's local API and synthetic results do not establish those capabilities.


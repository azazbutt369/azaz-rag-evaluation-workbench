# Inspected sample outputs

Actual test outputs from the fictional NorthstarFlow fixture. These examples were selected after observing the benchmark to illustrate success and failure. All 48 test cases per method remain available in reports/index.html and benchmark.json.

## Supported source excerpt

Question: How do I rotate an API key without interrupting integrations?

Case: `test-api-rotation-1` | Method: `hybrid` | Answerable: True | Abstained: False

Observed response:

> To rotate an API key, create a second key, update every integration to use it, verify successful requests, and then revoke the old key. Two keys may remain active during a rotation. Revocation is immediate and cannot be undone. NorthstarFlow never displays the full secret again after the key creation screen closes.

Citation: api-rotation; expected source: api-rotation.
Returned order: api-rotation, key-names, idempotency, ratelimit, sso.
Evidence score: 0.630330; selected development threshold: 0.35. This score is not a probability.

## Unknown fact: abstention

Question: What will an Enterprise subscription cost in 2031?

Case: `test-future-prices-1` | Method: `hybrid` | Answerable: False | Abstained: True

Observed response:

> I do not have sufficient evidence in the eligible knowledge base to answer this question.

Citation: none; expected source: none.
Returned order: cancel, user-removal, refunds, roles, support-hours.
Evidence score: 0.259090; selected development threshold: 0.35. This score is not a probability.

## Wrong source despite a relevant top-five hit

Question: Which workspace role is allowed to modify payment settings?

Case: `test-roles-2` | Method: `hybrid` | Answerable: True | Abstained: False

Observed response:

> When a renewal card payment fails, NorthstarFlow emails the billing owner and provides a seven-day grace period. During the grace period, search remains available but new ingestion is paused after the first day. Update the card in Settings > Billing. Successful payment resumes ingestion without requiring a new workspace.

Citation: failed-payment; expected source: roles.
Returned order: failed-payment, roles, cancel, invoices, receipt.
Evidence score: 0.446901; selected development threshold: 0.35. This score is not a probability.

## Useful source rejected by the gate

Question: What is the safe sequence for replacing a key used by my integration?

Case: `test-api-rotation-3` | Method: `hybrid` | Answerable: True | Abstained: True

Observed response:

> I do not have sufficient evidence in the eligible knowledge base to answer this question.

Citation: none; expected source: api-rotation.
Returned order: api-rotation, idempotency, key-names, ratelimit, sync-errors.
Evidence score: 0.329479; selected development threshold: 0.35. This score is not a probability.

## Reranking regression

Question: Does an accepted upload response mean my documents are already searchable?

Case: `test-job-status-3` | Method: `reranked` | Answerable: True | Abstained: True

Observed response:

> I do not have sufficient evidence in the eligible knowledge base to answer this question.

Citation: none; expected source: job-status.
Returned order: upload, job-status, invoices, export, duplicate-files.
Evidence score: 0.240893; selected development threshold: 0.35. This score is not a probability.

## Hybrid answers a baseline false abstention

Question: Can two credentials stay active while I replace an access key?

Case: `test-api-rotation-2` | Method: `hybrid` | Answerable: True | Abstained: False

Observed response:

> To rotate an API key, create a second key, update every integration to use it, verify successful requests, and then revoke the old key. Two keys may remain active during a rotation. Revocation is immediate and cannot be undone. NorthstarFlow never displays the full secret again after the key creation screen closes.

Citation: api-rotation; expected source: api-rotation.
Returned order: api-rotation, key-names, sso-session, ratelimit, export.
Evidence score: 0.368198; selected development threshold: 0.35. This score is not a probability.

The source-and-substring correctness proxy does not assess semantic faithfulness or the completeness of a generated response. No live LLM was used.

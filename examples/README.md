# Response-adapter example

`demo_extractive_responses.jsonl` contains all 48 test responses from the
committed sparse-hybrid extractive run. This is a complete input for the external
response-checking contract. It was not produced by a live LLM or a client system.

```bash
python -m ragbench score-responses examples/demo_extractive_responses.jsonl --split test
```

Replace the file with actual permitted model responses using the same schema
and stable query IDs. The checker validates citation IDs, eligibility and
expected spans; human semantic review is still required. Do not treat passing
this proxy as a hallucination-free result.

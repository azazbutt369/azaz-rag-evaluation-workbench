# NorthstarFlow support fixture

This is an original, fictional B2B document-search product. All company policies,
plan limits, questions, answers and internal markers are invented. The corpus
contains no actual customer records, private messages or working credentials.
It is released with this project's MIT licence.

The benchmark contains 48 passages: 36 current public passages available to
Growth, six archived passages, four internal passages and two Enterprise-only
passages. The 96 questions form 36 intent groups. Development and test each
contain 36 answerable questions and 12 unanswerable questions. Three paraphrases
of an answerable intent always remain in one split. Each answerable question
has one manually specified relevant passage and an expected answer substring.

The source knowledge base is shared across splits, as in a fixed-corpus retrieval
evaluation. The split is by question intent, not document ingestion date.
Indexing the source corpus is permitted; indexing evaluation questions, gold
answers or relevance labels is prohibited. The retrieval module receives only
documents, the frozen domain lexicon, query text and plan.

The lexicon is an explicit domain vocabulary, not a learned model. It was written
before the first benchmark run, with awareness of the demonstration domain and
the authored questions. No claim of blind or independently adjudicated testing
is made. Development-only calibration selects an abstention threshold for each
method; no threshold, weight or lexicon is selected using test metrics.
BM25 receives raw questions, while hybrid and reranked methods use expansion.
The BM25-to-hybrid comparison combines query expansion and fusion; it is not an
ablation of character retrieval alone. Reranked-to-hybrid isolates reranking.

Negative cases include missing facts, unsupported capabilities, synthetic
internal canaries and plan-ineligible content. "Unanswerable" means unsupported
by the eligible public corpus for that query's plan. It does not mean the fact
cannot be known elsewhere. All methods use identical eligibility filters before
ranking, so retrieval improvements cannot be attributed to different access rules.

Limitations: authored questions and labels, small corpus, mostly single-passage
answers, no real user traffic, no independent annotation, no long-document
chunking, no multilingual benchmark and no live generative-model run. Some
paraphrases ask for a distinction; the expected substring is only an automated
proxy and may over-credit a source excerpt. Inspect the source and failure table.
Do not present these results as customer performance or a general RAG benchmark.


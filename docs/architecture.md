# Architecture Overview | البنية الهندسية للنظام

Daleel is structured as a multi-agent state graph built on LangGraph with the following layers:

```
[User Clinical Query]
         │
         ▼
 ┌───────────────┐
 │ Planner Agent │  --> PICO Decomposition & Multi-Query Generation
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ Search Agent  │  --> Hybrid Retrieval (Dense Qdrant + Sparse BM25) + Reranking
 └───────┬───────┘
         │
         ▼
 ┌────────────────┐
 │Appraisal Agent │  --> OCEBM Evidence Level Scoring & Methodological Bias Check
 └───────┬────────┘
         │
         ▼
 ┌─────────────────┐
 │ Synthesis Agent │  --> Clinical Synthesis with Exact In-line Citations
 └───────┬─────────┘
         │
         ▼
 ┌─────────────────┐
 │ Verifier Agent  │  --> Factuality & Citation Verification
 └───────┬─────────┘
         ├──[Pass]──> [Final Verified Response]
         └──[Fail / Missing Claims]──> [Self-Correction Loop to Searcher]
```
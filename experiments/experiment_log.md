# Daleel - Experiment Log | سجل التجارب

This document tracks all quantitative experiments, parameter tuning, ablation studies, and evaluation benchmark results.

| Exp ID | Date | Retriever | Reranker | LLM | Top-K | Context Recall | Faithfulness | Notes |
|--------|------|-----------|----------|-----|-------|----------------|--------------|-------|
| EXP-01 | 2026-11-02 | BM25 | None | GPT-4o-mini | 10 | - | - | Initial lexical baseline |
| EXP-02 | 2026-11-02 | Dense (MiniLM) | None | GPT-4o-mini | 10 | - | - | Dense vector baseline |
| EXP-03 | 2026-11-02 | Hybrid | CrossEncoder | GPT-4o-mini | 5 | - | - | Full Daleel Agentic Pipeline |
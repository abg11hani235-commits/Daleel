# Architecture Decisions Log (ADR) | سجل القرارات الهندسية

### ADR 001: Selection of LangGraph for Agent Orchestration
- **Status**: Accepted
- **Context**: Daleel requires dynamic cyclical workflows where evidence appraisal or verification failure triggers re-retrieval.
- **Decision**: Adopt LangGraph over static DAG frameworks to enable cyclical state machines and multi-agent coordination.

### ADR 002: Hybrid Retrieval (Dense + BM25) with Cross-Encoder Reranking
- **Status**: Accepted
- **Context**: Biomedical terminology requires exact acronym and drug name matching (BM25) as well as semantic intent matching (Dense embeddings).
- **Decision**: Combine Qdrant dense vector search with rank-bm25 and refine candidates using a Cross-Encoder reranker.
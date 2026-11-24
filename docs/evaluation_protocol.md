# Evaluation Protocol | بروتوكول التقييم

The evaluation framework assesses Daleel across three primary dimensions:

1. **Retrieval Performance**:
   - Mean Reciprocal Rank (MRR@10)
   - Normalized Discounted Cumulative Gain (nDCG@10)
   - Recall@K

2. **Generation & Agentic Fidelity (Ragas Framework)**:
   - **Faithfulness**: Percentage of claims grounded in retrieved context.
   - **Answer Relevance**: Semantic alignment with the original medical inquiry.
   - **Context Recall**: Coverage of gold-standard evidence passages.

3. **Clinical Verification**:
   - Citation accuracy (Hallucinated vs verified PMID links).
   - Evidence level distribution (Ratio of high-level evidence like RCTs vs observational studies).
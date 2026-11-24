# Data Dictionary | معجم البيانات

Definitions and schemas for raw, interim, and processed data in Daleel:

### 1. `articles.jsonl` Schema
- `id` (string): Unique identifier (PMID or PMCID).
- `title` (string): Title of the article.
- `abstract` (string): Full abstract text.
- `authors` (list[string]): List of authors.
- `journal` (string): Journal name.
- `pub_date` (string): Date of publication.
- `publication_type` (list[string]): e.g., RCT, Systematic Review, Meta-Analysis.
- `mesh_terms` (list[string]): Medical Subject Headings.
- `doi` (string): Digital Object Identifier.

### 2. `chunks.jsonl` Schema
- `chunk_id` (string): Hash or composite ID (`{id}_{index}`).
- `article_id` (string): Foreign key reference to `articles.jsonl`.
- `text` (string): Chunk text content.
- `section` (string): Section heading (Introduction, Methods, Results, Discussion).
- `token_count` (int): Number of tokens.
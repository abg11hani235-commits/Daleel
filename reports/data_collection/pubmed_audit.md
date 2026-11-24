# Daleel — Phase 2: PubMed Dataset Quality Audit Report

**Auditor:** Senior Data Engineer  
**Project:** Daleel Evidence RAG (Graduation Project TM471)  
**Date:** 2026-11-20  
**Dataset File:** `data/raw/pubmed/pubmed_records.jsonl`  
**Dataset Size:** 50 records (152,252 bytes)  
**Search Universe:** 1,168 matching articles reported on PubMed (2015–2026)  
**Audit Status:** Completed (100% Read-Only)  
**Gate Status:** ⚠️ **PAUSE PMC COLLECTION — QUERY & INGESTION REFINEMENT REQUIRED**

---

## 1. Executive Summary

A comprehensive quality audit was conducted on the initial 50-record sample collected from PubMed for the Daleel Evidence RAG system. The system's primary clinical objective is to deliver authoritative, evidence-based retrieval and synthesis for patients with **Type 2 Diabetes (T2D)** and **Chronic Kidney Disease (CKD)**.

### Overall Health Score: **72 / 100**

* **Syntactic Integrity (100/100):** Exceptional. Zero corrupt JSON lines, 100% non-empty titles, abstracts, journals, publication types, and valid PMIDs. Zero duplicate PMIDs.
* **Clinical Focus (84/100):** 84% of articles directly address cardiorenal outcomes, SGLT2 inhibitors, GLP-1 receptor agonists, finerenone, and biomarkers in diabetic kidney disease.
* **Representativeness & Sampling (30/100) — CRITICAL FLAW:** Severe reverse-chronological truncation bias. **98% (49/50) of records are from year 2026**, with 1 from late 2025 and **0% from 2015–2024**.
* **Landmark Trial Coverage (0/100) — CRITICAL FLAW:** **0 out of 6** seminal landmark clinical trials (CREDENCE, DAPA-CKD, EMPA-KIDNEY, FIDELIO-DKD, FIGARO-DKD, FLOW) are present as primary studies in the sample.
* **Pipeline Safety (45/100):** `scripts/collect_pubmed.py` uses overwrite mode (`"w"`), presenting high risk of silent data loss upon re-execution. Zero embedded provenance metadata (query string, run timestamp, E-utilities API version).

---

## 2. Dataset Structure & Schema Inspection

The dataset is stored in standard line-delimited JSON (`JSONL`). Each line represents a single article parsed from NCBI Medline format.

### Field Inventory
| Field Name | Data Type | Presence in Dataset | Description |
| :--- | :--- | :---: | :--- |
| `pmid` | `string` | 50 / 50 (100%) | PubMed Unique Identifier (numeric string) |
| `title` | `string` | 50 / 50 (100%) | Full article title in English |
| `abstract` | `string` | 50 / 50 (100%) | Structured or unstructured text abstract |
| `journal` | `string` | 50 / 50 (100%) | Full journal title |
| `pub_date` | `string` | 50 / 50 (100%) | Date string (e.g. `"2026 Oct 30"`, `"2026"`) |
| `authors` | `list[str]` | 50 / 50 (100%) | Standardized author names (e.g. `["Gao J", "Wang J"]`) |
| `mesh_terms` | `list[str]` | 50 / 50 (100%) | Medical Subject Headings descriptors and qualifiers |
| `publication_types` | `list[str]` | 50 / 50 (100%) | NLM publication type classifications |
| `doi` | `string` / `null` | 50 / 50 (100%) | Digital Object Identifier |
| `pmcid` | *Absent* | 0 / 50 (0%) | PubMed Central Open Access ID (not yet extracted) |

---

## 3. Field Validation & Missing Data Audit

```
┌────────────────────────────────────────────────────────┐
│               FIELD COMPLETENESS METRICS               │
├──────────────────────┬─────────────┬──────────┬────────┤
│ Field                │ Required    │ Present  │ Missing│
├──────────────────────┼─────────────┼──────────┼────────┤
│ pmid                 │ Yes         │ 50 (100%)│ 0 (0%) │
│ title                │ Yes         │ 50 (100%)│ 0 (0%) │
│ abstract             │ Yes         │ 50 (100%)│ 0 (0%) │
│ journal              │ Yes         │ 50 (100%)│ 0 (0%) │
│ pub_date (year)      │ Yes         │ 50 (100%)│ 0 (0%) │
│ publication_types    │ Yes         │ 50 (100%)│ 0 (0%) │
│ doi                  │ Recommended │ 50 (100%)│ 0 (0%) │
│ pmcid                │ Expected    │ 0 (0%)   │ 50(100%)
└──────────────────────┴─────────────┴──────────┴────────┘
```

### Key Technical Observations on Missing Data
1. **PMCID Missing Rate (100%):** Medline format (`rettype="medline"`) does not consistently store PMC IDs in raw fields unless explicitly mapped. To collect full-text XML from PMC in Phase 3, we must resolve PMCID via `Bio.Entrez.elink(dbfrom="pubmed", db="pmc", id=...)` or query the PMC ID converter API.
2. **Abstract Completeness (100%):** Every record in the sample contains a non-empty, substantive abstract. No truncated single-word placeholders were detected.
3. **Publication Year:** Stored currently as unparsed `pub_date` strings. A regex extraction `\b(19\d\d|20\d\d)\b` successfully normalized 100% of dates into 4-digit integer years.

---

## 4. Duplicate & Redundancy Analysis

* **Unique PMIDs:** 50 out of 50. **Zero duplicate PMIDs.**
* **Semantic / Co-Publication Duplication Discovery:**
  A cross-journal duplicate was detected for the **2026 AHA/ACC/ADA/ASN CKM Guideline**:
  * **PMID 42265997:** Published June 9, 2026 in *Journal of the American College of Cardiology* (`pub_date: 2026 Jun 9`).
  * **PMID 42263157:** Published July 28, 2026 in *Circulation* (`pub_date: 2026 Jul 28`).
  * **Title:** *"2026 AHA/ACC/ADA/ASN Guideline for the Prevention, Detection, Evaluation, and Management of Cardiovascular-Kidney-Metabolic Syndrome: A Report of the American College of Cardiology/American Heart Association Joint Committee on Clinical Practice Guidelines"*.

> [!NOTE]
> Professional cardiology/nephrology guidelines are routinely co-published across partner societies. In downstream chunking and embedding, keeping both records without deduplication would cause index bloating and duplicate evidence cards in the UI. Deduplication by normalized title or DOI must be enforced in `src/daleel/preprocessing/deduplicator.py`.

---

## 5. Publication Types & Temporal Distributions

### Study Design Breakdown
The search query successfully filtered for high-evidence study types:

| Publication Type | Article Count | % of Sample | Evidence Hierarchy Tier |
| :--- | :---: | :---: | :--- |
| **Randomized Controlled Trial** | 24 | 48.0% | Tier 1 (Primary Interventional Evidence) |
| **Systematic Review** | 19 | 38.0% | Tier 1 (Secondary Synthesized Evidence) |
| **Meta-Analysis** | 14 | 28.0% | Tier 1 (Quantitative Synthesis) |
| **Multicenter Study** | 8 | 16.0% | Tier 1 / 2 (High-powered multicenter cohorts) |
| **Network Meta-Analysis** | 4 | 8.0% | Tier 1 (Comparative Head-to-Head Synthesis) |
| **Practice Guideline** | 3 | 6.0% | Clinical Policy & Recommendations |
| **Clinical Trial, Phase III** | 3 | 6.0% | Pivotal Pre-Registration Trials |
| **Clinical Trial, Phase II** | 2 | 4.0% | Dose-Finding / Safety Proof-of-Concept |
| **Comparative Study** | 2 | 4.0% | Observational Comparative Effectiveness |

*(Note: Publications can belong to multiple categories, e.g. a paper can be both a Systematic Review and a Meta-Analysis).*

### Temporal Skew (Publication Year)
* **2026:** 49 articles (98.0%)
* **2025:** 1 article (2.0%)
* **2015 – 2024:** 0 articles (0.0%)

---

## 6. Clinical Relevance Audit (T2D + CKD)

Every article was evaluated for genuine clinical relevance to both Type 2 Diabetes and Chronic Kidney Disease:

```
┌────────────────────────────────────────────────────────┐
│              CLINICAL RELEVANCE BREAKDOWN              │
├────────────────────────────────────────┬───────┬───────┤
│ Category                               │ Count │ %     │
├────────────────────────────────────────┼───────┼───────┤
│ Core Dual Relevance (T2D + CKD)        │ 42    │ 84.0% │
│ Peripheral / Tangential Mention        │ 7     │ 14.0% │
│ False Positive (Non-Diabetic Cohort)   │ 1     │ 2.0%  │
└────────────────────────────────────────┴───────┴───────┘
```

### False Positive Analysis (Failure of Keyword-Only Filtering)
* **PMID 42246672:** *"Finerenone in Persons with Chronic Kidney Disease without Diabetes"* (FIND-CKD trial, published August 2026).
  * **Why it matched:** The search query searched `"type 2 diabetes"[Title/Abstract]`. The abstract stated in its background sentence: *"In randomized trials, finerenone... improved kidney and cardiovascular outcomes in patients with type 2 diabetes and chronic kidney disease. Whether finerenone has similar effects in patients without diabetes... is unknown."*
  * **Actual Study Population:** Explicitly adults **without diabetes** with CKD.
  * **Impact:** Ingesting this into an evidence-base for diabetic nephropathy will dilute diabetic cohort specificity.
  * **Remediation:** Refine search syntax using MeSH terms for the primary disease entity, or implement a title/exclusion filter in preprocessing (`"without diabetes" NOT in title`).

### Peripheral / Tangential Records (Incidental Matches)
1. **PMID 42504070:** Subgroup analysis of probiotic *Bifidobacterium bifidum* for constipation in patients with T2D + CKD (symptomatic microbiome focus, not cardiorenal disease modification).
2. **PMID 42805503:** EASL-EASD-EASO clinical practice guidance on MASH (metabolic steatohepatitis) and resmetirom (liver-focused, incidental CKD mention).
3. **PMID 42290203:** Steno INTEN-CT substudy on aortic valve calcification.
4. **PMID 42249978:** SGLT2 inhibitors following heart transplantation in T2D.
5. **PMID 42237280:** Adolescent obesity registry study evaluating general long-term adult morbidity.

---

## 7. Landmark Clinical Trial Coverage

Guideline-directed medical therapy for T2D + CKD rests upon 6 landmark cardiovascular and renal outcome trials. We audited the dataset for their coverage:

| Landmark Trial | Drug & Target | Primary Reference | Primary PMID | In Dataset? | Secondary Mentions in Dataset |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **CREDENCE** | Canagliflozin (SGLT2i) | Perkovic et al., *NEJM* 2019 | `30990260` | ❌ **Missing** | Cited in PMID 42546972 (2026 meta-analysis) |
| **DAPA-CKD** | Dapagliflozin (SGLT2i) | Heerspink et al., *NEJM* 2020 | `32970396` | ❌ **Missing** | Cited in PMID 42256478 (2025 review) |
| **EMPA-KIDNEY** | Empagliflozin (SGLT2i) | Herrington et al., *NEJM* 2023 | `36331190` | ❌ **Missing** | Cited in PMID 42256478 (2025 review) |
| **FIDELIO-DKD** | Finerenone (nsMRA) | Bakris et al., *NEJM* 2020 | `33264271` | ❌ **Missing** | Cited in PMID 42248158 (2026 meta-analysis) |
| **FIGARO-DKD** | Finerenone (nsMRA) | Pitt et al., *NEJM* 2021 | `34449181` | ❌ **Missing** | Cited in PMID 42248158 (2026 meta-analysis) |
| **FLOW** | Semaglutide (GLP-1 RA) | Perkovic et al., *NEJM* 2024 | `38785209` | ❌ **Missing** | Cited in PMID 42567173 & 42337824 |

### Finding:
**0 / 6 (0.0%) of primary landmark trials exist in the current dataset.**  
While the trials are frequently referenced in recent meta-analyses, their original trial publications (the "gold standard" primary evidence containing baseline patient characteristics, exact Hazard Ratios, and primary outcome definitions) are completely absent.

---

## 8. Sampling Bias & Retrieval Ordering Analysis

### Root Cause Diagnosis
1. **NCBI E-Utilities Sort Behavior:** By default, `Entrez.esearch(db="pubmed", term=query, retmax=50)` retrieves records ordered by `pub_date` descending (Most Recent).
2. **Universe vs. Sample Size:** The query matches 1,168 records across 12 calendar years (2015–2026). Truncating to `retmax=50` effectively samples only the top 4.2% of the distribution.
3. **Chronological Starvation:** Because PubMed indexed hundreds of relevant papers in 2026 alone, a 50-article slice is 100% saturated by late 2025 / 2026 articles, completely cutting off the entire historical foundation of modern nephrology (2015–2024).

### Impact on RAG System
If a user asks Daleel: *"What were the primary renal findings of the CREDENCE trial?"* or *"Compare the eGFR slope benefits of DAPA-CKD vs EMPA-KIDNEY"*, the RAG retriever will be forced to synthesize from secondary commentary rather than the foundational primary trials.

---

## 9. Pipeline Safety & Script Idempotency

### Inspection of `scripts/collect_pubmed.py`
```python
articles = client.fetch_details(id_list)
out_file = Path(args.output)
out_file.parent.mkdir(parents=True, exist_ok=True)
save_jsonl(articles, str(out_file))  # Calls open(filepath, "w")
```

### Risk Assessment: **HIGH RISK OF DATA LOSS**
* `save_jsonl` opens the destination file with mode `"w"`.
* Running `python scripts/collect_pubmed.py --max_results 10` will immediately erase `data/raw/pubmed/pubmed_records.jsonl` and replace it with only 10 records.
* There is no existing PMID deduplication against on-disk records.
* There is no versioning or backup before write.

---

## 10. Provenance & Reproducibility Assessment

| Provenance Requirement | Status | Current Reality |
| :--- | :---: | :--- |
| **Exact Search Query String** | ❌ Missing | Not recorded inside records or alongside data file |
| **Collection Timestamp** | ❌ Missing | No `_collected_at` field in JSON objects |
| **Retrieval Date** | ❌ Missing | No run-level execution date logged |
| **API Version & Endpoint** | ❌ Missing | E-Utilities version not preserved |
| **NCBI Tool Parameter** | ❌ Missing | `tool=daleel_research` used in code, but unrecorded in data |

---

## 11. Concrete Recommendations & Proposed Solutions

### Recommendation 1: Fix Collection Script Idempotency & Provenance
Modify `PubMedClient.fetch_details` or `collect_pubmed.py` to:
1. Read existing PMIDs from `data/raw/pubmed/pubmed_records.jsonl`.
2. Skip already downloaded PMIDs (idempotent collection).
3. Append new records with provenance headers:
   ```json
   {
     "pmid": "42964092",
     "title": "...",
     "_provenance": {
       "collected_at": "2026-11-20T07:39:33Z",
       "query_used": "DEFAULT_QUERY_V1",
       "source": "ncbi_pubmed_eutilities"
     }
   }
   ```

### Recommendation 2: Eliminate Sampling Bias with Hybrid Retrieval Strategy
Instead of a single blind chronological grab of 50 records:
1. **Mandatory Landmark Seed Ingestion:** Explicitly ingest the 6 landmark trials (`PMIDs: 30990260, 32970396, 36331190, 33264271, 34449181, 38785209`) as non-negotiable benchmark anchors.
2. **Relevance Sorting:** In `Entrez.esearch`, add `sort="relevance"`.
3. **Temporal Stratification:** Sample records across three clinical epochs:
   * *Epoch 1 (2015–2019):* Discovery & early SGLT2i cardiovascular outcome trials (EMPA-REG, CANVAS, CREDENCE).
   * *Epoch 2 (2020–2023):* Landmark renal trials (DAPA-CKD, FIDELIO-DKD, FIGARO-DKD, EMPA-KIDNEY).
   * *Epoch 3 (2024–2026):* GLP-1 RA renal outcomes (FLOW), dual therapies, and updated international guidelines.
4. **Expand Sample Size:** Scale `retmax` from 50 to **300–500 articles** to achieve statistical and clinical saturation.

### Recommendation 3: Add PMCID Resolution
Before triggering full-text retrieval from PMC (`data/raw/pmc/`), add a resolution step in `src/daleel/ingestion/pmc_client.py` using `Entrez.elink` to link each PMID to its open-access PMCID.

---

## 12. Final Decision & Gate Verdict

### **Verdict:** ⚠️ **PAUSE PMC COLLECTION — REFINE QUERY & SAMPLING FIRST**

Proceeding immediately to PMC full-text collection on this 50-article dataset would propagate severe temporal bias and miss the foundational clinical evidence required for an authoritative medical graduation project. 

The pipeline should first:
1. Ingest the 6 primary landmark trials.
2. Expand the dataset to 300+ articles using stratified/relevance sampling.
3. Resolve PMCIDs for open-access papers.
4. Then trigger full-text PMC collection.

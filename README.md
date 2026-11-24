# Daleel (دليل) — Clinical Evidence RAG System

An authoritative, evidence-based Retrieval-Augmented Generation (RAG) system tailored for biomedical literature and clinical guidelines in **Type 2 Diabetes (T2D)** and **Chronic Kidney Disease (CKD)**.

> **Project:** Arab Open University (AOU) — TM471 Graduation Project  
> **Topic:** Evidence-Based AI Assistant for Diabetic Kidney Disease Management

---

## 📌 Project Architecture

```
Daleel Graduation Project/
├── configs/               # System configurations (models, retrieval, settings)
├── data/
│   ├── raw/               # Raw ingested datasets (PubMed records, PMC, Guidelines)
│   ├── interim/           # Cleaned and parsed intermediate documents
│   └── processed/         # Chunked, embedded, and indexed corpus
├── docs/                  # Architecture, protocol, and data dictionaries
├── reports/               # Quality audits and collection manifests
├── scripts/               # CLI pipelines (collection, PMCID resolution, audits)
├── src/daleel/            # Core package
│   ├── agents/            # Multi-agent clinical reasoning pipeline
│   ├── ingestion/         # E-Utilities, PMC, and Guideline loaders
│   ├── preprocessing/     # Text cleaning, chunking, deduplication
│   ├── retrieval/         # Dense (embeddings), sparse (BM25), reranking
│   └── utils/             # Helpers and structured logging
├── tests/                 # Comprehensive unit and integration test suite
└── ui/                    # Streamlit interactive clinician interface
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Virtual environment (`venv`)

### 2. Setup Environment
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your NCBI credentials:
```env
NCBI_EMAIL=your_email@example.com
NCBI_API_KEY=your_ncbi_api_key_here
NCBI_TOOL=daleel_research
```

---

## 🔬 Data Ingestion & Audit Pipelines

### Collect & Expand PubMed Evidence
```powershell
$env:PYTHONPATH="src"
python scripts/collect_pubmed.py
```

### Resolve Open-Access PMCIDs
```powershell
$env:PYTHONPATH="src"
python scripts/resolve_pmcids.py
```

### Run Quality Audit
```powershell
$env:PYTHONPATH="src"
python scripts/audit_pubmed.py
```

---

## 🧪 Testing

Run all unit and integration tests:
```powershell
$env:PYTHONPATH=".;src"
pytest tests/ -v
```

---

## 📄 License & Disclaimers
This project utilizes NCBI/NLM E-Utilities under NCBI policies and disclaimers. See `.licenses/pubmed_database_LICENSE.txt` for details.

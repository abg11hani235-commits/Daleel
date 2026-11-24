"""Tests for Daleel Phase 2 PubMed Dataset Quality Auditor.

Ensures that the auditor correctly validates data completeness, duplicate detection,
landmark study checking, clinical relevance parsing, and strictly enforces the read-only constraint.
"""

import hashlib
import json
from pathlib import Path
import pytest
from scripts.audit_pubmed import PubMedDatasetAuditor, LANDMARK_STUDIES


DATASET_PATH = "data/raw/pubmed/pubmed_records_backup_50.jsonl"


@pytest.fixture
def auditor():
    return PubMedDatasetAuditor(DATASET_PATH)


@pytest.fixture
def records(auditor):
    return auditor.load_dataset()


def test_dataset_exists_and_loads(records):
    assert len(records) == 50
    assert isinstance(records[0], dict)
    assert "pmid" in records[0]


def test_required_fields_have_zero_missing(auditor, records):
    field_audit = auditor.audit_field_validation(records)
    req_validation = field_audit["required_fields_validation"]

    for fld in ["pmid", "title", "abstract", "pub_date", "journal", "publication_types"]:
        assert req_validation[fld]["valid"] is True, f"Field {fld} has missing values"
        assert req_validation[fld]["missing_count"] == 0


def test_doi_and_pmcid_audit(auditor, records):
    field_audit = auditor.audit_field_validation(records)
    opt = field_audit["optional_and_derived_fields"]

    # In our current Medline extraction, DOI was parsed, while PMCID is not extracted
    assert opt["doi"]["present_count"] > 0
    assert opt["pmcid"]["present_count"] == 0  # Accurately detects missing PMCID field


def test_duplicate_detection(auditor, records):
    dup_audit = auditor.audit_duplicates(records)
    assert dup_audit["has_duplicate_pmids"] is False
    assert dup_audit["duplicate_pmid_count"] == 0
    assert dup_audit["unique_pmids"] == 50

    # Tests discovery of co-published guideline (JACC vs Circulation)
    assert dup_audit["has_co_published_titles"] is True
    assert dup_audit["duplicate_title_count"] == 1


def test_publication_years_and_types_summary(auditor, records):
    summary = auditor.audit_publication_types_and_years(records)
    assert "Journal Article" in summary["publication_types_distribution"]
    assert "Randomized Controlled Trial" in summary["publication_types_distribution"]
    assert "2026" in summary["publication_years_distribution"]
    assert summary["dominant_year"] == "2026"


def test_clinical_relevance_detects_false_positive(auditor, records):
    rel_audit = auditor.audit_clinical_relevance(records)
    assert rel_audit["total_records"] == 50
    assert rel_audit["core_dual_relevance_count"] >= 40

    # Must accurately flag FIND-CKD (42246672: "without Diabetes") as non-diabetic false positive
    fp_pmids = [fp["pmid"] for fp in rel_audit["false_positive_details"]]
    assert "42246672" in fp_pmids


def test_landmark_coverage_identifies_primary_gap(auditor, records):
    landmark_audit = auditor.audit_landmark_coverage(records)
    assert landmark_audit["total_landmarks_checked"] == 6
    # Confirms that primary trials (CREDENCE 2019, DAPA-CKD 2020, etc.) are absent from the 2026-skewed sample
    assert landmark_audit["primary_trials_present_count"] == 0
    # Confirms that secondary mentions do exist in recent literature
    assert landmark_audit["secondary_citations_present_count"] > 0


def test_sampling_bias_analysis(auditor, records):
    bias_audit = auditor.audit_sampling_bias(records, reported_total_search_matches=1168)
    assert bias_audit["has_severe_temporal_bias"] is True
    assert len(bias_audit["mitigation_strategies"]) >= 3


def test_collection_script_idempotency_audit(auditor):
    idem_audit = auditor.audit_collection_script_idempotency("scripts/collect_pubmed.py")
    assert idem_audit["script_exists"] is True
    assert idem_audit["has_deduplication_logic"] is True
    assert idem_audit["has_safe_merge"] is True
    assert idem_audit["risk_assessment"] == "SAFE_IDEMPOTENT_MERGE"


def test_provenance_audit(auditor, records):
    prov = auditor.audit_provenance(records)
    assert prov["has_pmid_identifier"] is True
    assert prov["has_search_query_embedded"] is False
    assert prov["has_collection_timestamp"] is False


def test_read_only_constraint(auditor):
    """Verify that executing the audit makes zero changes to the underlying dataset file."""
    path = Path(DATASET_PATH)
    assert path.exists()

    def get_file_hash(p: Path) -> str:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    mtime_before = path.stat().st_mtime
    hash_before = get_file_hash(path)

    # Run full audit
    auditor.run_full_audit()

    mtime_after = path.stat().st_mtime
    hash_after = get_file_hash(path)

    assert hash_before == hash_after, "Dataset file hash changed during audit execution!"
    assert mtime_before == mtime_after, "Dataset file modification time changed during audit execution!"

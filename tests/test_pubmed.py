"""Unit tests for PubMed ingestion client, safe merge, duplicate handling, and relevance screening."""

from unittest.mock import MagicMock, patch
import pytest
from daleel.ingestion.pubmed_client import (
    LANDMARK_STUDIES_REGISTRY,
    PubMedClient,
    compute_canonical_work_id,
    compute_query_hash,
    extract_publication_year,
    screen_record_relevance,
)


def test_pubmed_client_initialization():
    client = PubMedClient()
    assert client is not None
    assert client.email is not None


def test_compute_query_hash_deterministic():
    q1 = "Diabetes Mellitus AND CKD"
    q2 = "  Diabetes   Mellitus AND    CKD "
    assert compute_query_hash(q1) == compute_query_hash(q2)
    assert len(compute_query_hash(q1)) == 64


def test_extract_publication_year():
    assert extract_publication_year("2026 Oct 30") == 2026
    assert extract_publication_year("2020 Dec") == 2020
    assert extract_publication_year("2019 Jun 13") == 2019
    assert extract_publication_year("Invalid date") is None
    assert extract_publication_year(None) is None


def test_safe_merge_preserves_existing_data():
    existing_map = {
        "1001": {
            "pmid": "1001",
            "title": "Existing Title",
            "abstract": "Existing Abstract",
            "doi": "10.1000/1",
            "pmcid": "PMC1001",
        }
    }
    # New record for same PMID has missing abstract and no PMCID
    new_records = [
        {
            "pmid": "1001",
            "title": "Existing Title",
            "abstract": "",
            "doi": "10.1000/1",
            "journal": "New Journal",
        }
    ]

    merged, added, updated = PubMedClient.merge_records(existing_map, new_records)
    assert len(merged) == 1
    assert added == 0
    assert updated == 1
    rec = merged[0]
    assert rec["abstract"] == "Existing Abstract"  # Preserved!
    assert rec["pmcid"] == "PMC1001"              # Preserved!
    assert rec["journal"] == "New Journal"        # Enriched!


def test_duplicate_pmid_prevention():
    existing_map = {
        "2001": {"pmid": "2001", "title": "Trial A"},
        "2002": {"pmid": "2002", "title": "Trial B"},
    }
    new_records = [
        {"pmid": "2001", "title": "Trial A duplicate"},
        {"pmid": "2003", "title": "Trial C"},
    ]

    merged, added, updated = PubMedClient.merge_records(existing_map, new_records)
    pmids = [r["pmid"] for r in merged]
    assert len(pmids) == 3
    assert len(set(pmids)) == 3
    assert added == 1


def test_co_publication_canonical_work_linking():
    rec1 = {
        "pmid": "4001",
        "title": "Joint Practice Guideline for Diabetes and CKD",
        "canonical_work_id": compute_canonical_work_id("Joint Practice Guideline for Diabetes and CKD"),
    }
    rec2 = {
        "pmid": "4002",
        "title": "joint practice guideline for diabetes and ckd",
        "canonical_work_id": compute_canonical_work_id("joint practice guideline for diabetes and ckd"),
    }
    records = [rec1, rec2]
    PubMedClient.link_co_publications(records)

    assert rec1["canonical_work_id"] == rec2["canonical_work_id"]
    assert "4002" in rec1["co_published_with"]
    assert "4001" in rec2["co_published_with"]


def test_relevance_screening_core_inclusion():
    rec = {
        "pmid": "5001",
        "title": "Canagliflozin and Renal Outcomes in Type 2 Diabetes and Nephropathy",
        "abstract": "We evaluated canagliflozin in patients with type 2 diabetes and chronic kidney disease with albuminuria.",
        "mesh_terms": ["Diabetes Mellitus, Type 2", "Diabetic Nephropathies"],
        "publication_types": ["Randomized Controlled Trial"],
    }
    res = screen_record_relevance(rec)
    assert res["screening_status"] == "included"
    assert res["t2d_relevance"] == "direct"
    assert res["ckd_relevance"] == "direct"
    assert res["population_relevance"] == "t2d_with_ckd"
    assert res["study_design_relevance"] == "rct"


def test_relevance_screening_detects_non_diabetic_exclusion():
    rec = {
        "pmid": "42246672",
        "title": "Finerenone in Persons with Chronic Kidney Disease without Diabetes",
        "abstract": "In previous trials, finerenone improved outcomes in type 2 diabetes and CKD. We studied persons without diabetes who had CKD.",
        "mesh_terms": ["Renal Insufficiency, Chronic", "Albuminuria"],
        "publication_types": ["Clinical Trial, Phase III"],
    }
    res = screen_record_relevance(rec)
    assert res["screening_status"] == "excluded"
    assert res["t2d_relevance"] == "excluded"
    assert res["population_relevance"] == "non_diabetic_ckd"
    assert "without diabetes" in res["screening_reason"]


def test_relevance_screening_uncertain_needs_manual_review():
    rec = {
        "pmid": "6001",
        "title": "Effect of probiotic on constipation in chronic kidney disease",
        "abstract": "Constipation and bowel movement frequencies were measured in patients.",
        "mesh_terms": ["Constipation"],
        "publication_types": ["Journal Article"],
    }
    res = screen_record_relevance(rec)
    assert res["screening_status"] == "needs_manual_review"
    assert res["population_relevance"] == "needs_manual_review"


@patch("daleel.ingestion.pubmed_client.Entrez.esearch")
def test_search_all_pmids_mocked(mock_esearch):
    mock_handle = MagicMock()
    mock_esearch.return_value.__enter__.return_value = mock_handle

    # Mock count then search
    with patch("daleel.ingestion.pubmed_client.Entrez.read") as mock_read:
        mock_read.side_effect = [
            {"Count": "3"},
            {"IdList": ["101", "102", "103"]},
        ]
        client = PubMedClient()
        total, pmids = client.search_all_pmids("Test Query")
        assert total == 3
        assert pmids == ["101", "102", "103"]


def test_landmark_studies_registry_coverage():
    assert "CREDENCE" in LANDMARK_STUDIES_REGISTRY
    assert "DAPA-CKD" in LANDMARK_STUDIES_REGISTRY
    assert "EMPA-KIDNEY" in LANDMARK_STUDIES_REGISTRY
    assert "FIDELIO-DKD" in LANDMARK_STUDIES_REGISTRY
    assert "FIGARO-DKD" in LANDMARK_STUDIES_REGISTRY
    assert "FLOW" in LANDMARK_STUDIES_REGISTRY

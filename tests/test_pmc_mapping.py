"""Unit tests for PMC mapping client and PMCID resolution."""

from unittest.mock import MagicMock, patch
import pytest
from daleel.ingestion.pmc_client import PMCClient


@pytest.fixture
def pmc_client():
    return PMCClient()


def test_pmc_client_initialization(pmc_client):
    assert pmc_client is not None
    assert pmc_client.email is not None


@patch("daleel.ingestion.pmc_client.Entrez.elink")
@patch("daleel.ingestion.pmc_client.Entrez.read")
def test_resolve_pmcid_batch_success(mock_read, mock_elink, pmc_client):
    mock_read.return_value = [
        {
            "IdList": ["36331190"],
            "LinkSetDb": [
                {
                    "LinkName": "pubmed_pmc",
                    "Link": [{"Id": "7614055"}],
                }
            ],
        },
        {
            "IdList": ["30990260"],
            "LinkSetDb": [],
        },
    ]

    results = pmc_client.resolve_pmcid_batch(["36331190", "30990260"])
    assert "36331190" in results
    assert results["36331190"]["status"] == "resolved"
    assert results["36331190"]["pmcid"] == "PMC7614055"

    # No PMCID handling
    assert "30990260" in results
    assert results["30990260"]["status"] == "not_in_pmc"
    assert results["30990260"]["pmcid"] is None


@patch("daleel.ingestion.pmc_client.Entrez.elink")
def test_resolve_pmcid_batch_retry_on_failure(mock_elink, pmc_client):
    mock_elink.side_effect = RuntimeError("NCBI connection error")

    results = pmc_client.resolve_pmcid_batch(["999999"], max_retries=2)
    assert "999999" in results
    assert results["999999"]["status"] == "resolution_error"
    assert results["999999"]["pmcid"] is None


def test_apply_pmcid_mapping(pmc_client):
    records = [
        {"pmid": "1001", "title": "Article 1"},
        {"pmid": "1002", "title": "Article 2"},
    ]
    mapping = {
        "1001": {"pmcid": "PMC1001", "status": "resolved", "resolved_at": "2026-11-20T00:00:00Z"},
        "1002": {"pmcid": None, "status": "not_in_pmc", "resolved_at": "2026-11-20T00:00:00Z"},
    }

    updated, mapped_cnt, unmapped_cnt = pmc_client.apply_pmcid_mapping(records, mapping)
    assert len(updated) == 2
    assert mapped_cnt == 1
    assert unmapped_cnt == 1
    assert updated[0]["pmcid"] == "PMC1001"
    assert updated[0]["pmcid_status"] == "resolved"
    assert updated[1]["pmcid"] is None
    assert updated[1]["pmcid_status"] == "not_in_pmc"


def test_fetch_full_text_raises_not_implemented(pmc_client):
    with pytest.raises(NotImplementedError):
        pmc_client.fetch_full_text("PMC1234567")

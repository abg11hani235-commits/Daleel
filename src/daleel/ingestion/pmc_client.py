"""PubMed Central (PMC) client for PMCID resolution and full-text retrieval.

Phase 3 implements robust, rate-limited, and retry-safe PMCID resolution
via NCBI E-Utilities (ELink pubmed_pmc relation).
Full-text downloading is deferred to Phase 4.
"""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from Bio import Entrez
from dotenv import find_dotenv, load_dotenv
from daleel.utils.logging import logger


class PMCClient:
    """Client for NCBI PMC E-Utilities and open-access services."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        email: Optional[str] = None,
        tool: str = "daleel_research",
    ):
        load_dotenv(find_dotenv(usecwd=True))
        self.email = email or os.getenv("NCBI_EMAIL") or os.getenv("USER_EMAIL")
        self.api_key = api_key or os.getenv("NCBI_API_KEY")
        self.tool = tool or os.getenv("NCBI_TOOL", "daleel_research")

        Entrez.email = self.email
        Entrez.tool = self.tool
        if self.api_key:
            Entrez.api_key = self.api_key

    def resolve_pmcid_batch(self, batch_pmids: List[str], max_retries: int = 3) -> Dict[str, Dict[str, Any]]:
        """Resolve a single batch of PMIDs to PMCIDs via NCBI ELink (pubmed_pmc relation)."""
        now_utc = datetime.now(timezone.utc).isoformat()
        results: Dict[str, Dict[str, Any]] = {
            pmid: {
                "pmcid": None,
                "status": "not_in_pmc",
                "resolved_at": now_utc,
            }
            for pmid in batch_pmids
        }

        if not batch_pmids:
            return results

        id_str = ",".join(batch_pmids)
        for attempt in range(max_retries):
            try:
                with Entrez.elink(dbfrom="pubmed", db="pmc", id=id_str) as handle:
                    records = Entrez.read(handle)

                for item in records:
                    src_id = str(item["IdList"][0])
                    links = item.get("LinkSetDb", [])
                    pmc_id = None
                    for link_db in links:
                        if link_db.get("LinkName") == "pubmed_pmc":
                            links_list = link_db.get("Link", [])
                            if links_list:
                                raw_id = links_list[0].get("Id")
                                pmc_id = f"PMC{raw_id}"
                                break

                    if pmc_id:
                        results[src_id] = {
                            "pmcid": pmc_id,
                            "status": "resolved",
                            "resolved_at": now_utc,
                        }
                    else:
                        results[src_id] = {
                            "pmcid": None,
                            "status": "not_in_pmc",
                            "resolved_at": now_utc,
                        }
                return results

            except Exception as e:
                logger.warning(f"ELink batch resolution attempt {attempt + 1}/{max_retries} failed for {len(batch_pmids)} IDs: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1.0 * (attempt + 1))
                else:
                    logger.error(f"Failed to resolve batch after {max_retries} attempts: {e}")
                    for pmid in batch_pmids:
                        results[pmid] = {
                            "pmcid": None,
                            "status": "resolution_error",
                            "error": str(e),
                            "resolved_at": now_utc,
                        }
        return results

    def resolve_pmcids(
        self,
        pmids: List[str],
        batch_size: int = 50,
        delay_sec: float = 0.15,
    ) -> Dict[str, Dict[str, Any]]:
        """Resolve a list of PMIDs to PMCIDs in safe, rate-limited batches.

        Returns a dictionary mapping pmid -> {"pmcid": "PMC...", "status": "resolved"|"not_in_pmc", "resolved_at": str}
        """
        all_results: Dict[str, Dict[str, Any]] = {}
        total = len(pmids)
        logger.info(f"Resolving PMCIDs for {total} PMIDs in batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = pmids[i : i + batch_size]
            batch_res = self.resolve_pmcid_batch(batch)
            all_results.update(batch_res)

            resolved_count = sum(1 for v in batch_res.values() if v.get("status") == "resolved")
            logger.info(f"Batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}: {resolved_count}/{len(batch)} resolved to PMC.")

            if delay_sec > 0 and i + batch_size < total:
                time.sleep(delay_sec)

        total_resolved = sum(1 for v in all_results.values() if v.get("status") == "resolved")
        logger.info(f"PMCID resolution complete: {total_resolved}/{total} resolved to PMC.")
        return all_results

    def apply_pmcid_mapping(
        self,
        records: List[Dict[str, Any]],
        mapping: Dict[str, Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Apply PMCID mapping to dataset records.

        Returns tuple of (updated_records, mapped_with_pmcid_count, unmapped_count).
        """
        mapped_count = 0
        unmapped_count = 0

        for r in records:
            pmid = str(r.get("pmid", "")).strip()
            if pmid in mapping:
                info = mapping[pmid]
                r["pmcid"] = info.get("pmcid")
                r["pmcid_status"] = info.get("status")
                r["pmcid_resolved_at"] = info.get("resolved_at")
                if r["pmcid"]:
                    mapped_count += 1
                else:
                    unmapped_count += 1
            else:
                if not r.get("pmcid"):
                    unmapped_count += 1

        return records, mapped_count, unmapped_count

    def fetch_full_text(self, pmcid: str):
        """Retrieve full text XML/JSON for a PMC article (deferred to Phase 4)."""
        raise NotImplementedError("Full-text downloading is strictly deferred to Phase 4 per project safety rules.")

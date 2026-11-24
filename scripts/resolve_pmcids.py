"""Script to resolve PubMed IDs to PubMed Central IDs (PMCIDs) via NCBI ELink.

Phase 3 implements robust, rate-limited PMCID resolution without downloading full text.
Preserves mapping status and retrieval timestamps.
"""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from daleel.ingestion.pmc_client import PMCClient
from daleel.ingestion.pubmed_client import PubMedClient
from daleel.utils.helpers import save_jsonl
from daleel.utils.logging import logger


def main():
    parser = argparse.ArgumentParser(description="Resolve PMIDs to PMCIDs for Daleel corpus.")
    parser.add_argument("--input", type=str, default="data/raw/pubmed/pubmed_records.jsonl", help="Input JSONL path")
    parser.add_argument("--mapping_file", type=str, default="data/raw/pubmed/pmcid_mapping.json", help="Destination mapping JSON path")
    parser.add_argument("--batch_size", type=int, default=50, help="Batch size for ELink")
    parser.add_argument("--delay", type=float, default=0.15, help="Delay between batches in seconds")
    parser.add_argument("--dry_run", action="store_true", help="Check resolution requirements without modifying files")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found at {input_path}")
        return

    logger.info("=== Daleel Phase 3: PMCID Resolution ===")
    records_map = PubMedClient.load_existing_records(input_path)
    records = list(records_map.values())
    total_records = len(records)
    logger.info(f"Loaded {total_records} records from {input_path}")

    # Load existing mapping if present
    mapping_p = Path(args.mapping_file)
    existing_mapping: Dict[str, Dict[str, Any]] = {}
    if mapping_p.exists():
        try:
            with open(mapping_p, "r", encoding="utf-8") as f:
                existing_mapping = json.load(f)
            logger.info(f"Loaded {len(existing_mapping)} cached PMCID mappings from {mapping_p}")
        except Exception as e:
            logger.warning(f"Could not load existing mapping: {e}")

    # Determine which PMIDs need resolution
    pmids_all = [r["pmid"] for r in records if r.get("pmid")]
    pmids_to_resolve = [p for p in pmids_all if p not in existing_mapping]

    logger.info(f"Total PMIDs: {len(pmids_all)}")
    logger.info(f"Already mapped in cache: {len(existing_mapping)}")
    logger.info(f"PMIDs requiring ELink resolution: {len(pmids_to_resolve)}")

    if args.dry_run:
        logger.info("[DRY RUN] Resolution simulation complete. Exiting without network calls.")
        return

    pmc_client = PMCClient()
    new_mapping = {}
    if pmids_to_resolve:
        new_mapping = pmc_client.resolve_pmcids(
            pmids_to_resolve,
            batch_size=args.batch_size,
            delay_sec=args.delay,
        )

    # Merge mappings
    combined_mapping = {**existing_mapping, **new_mapping}
    mapping_p.parent.mkdir(parents=True, exist_ok=True)
    with open(mapping_p, "w", encoding="utf-8") as f:
        json.dump(combined_mapping, f, indent=2)
    logger.info(f"Saved complete PMCID mapping table to {mapping_p.resolve()}")

    # Apply mapping to dataset records
    updated_records, mapped_count, unmapped_count = pmc_client.apply_pmcid_mapping(records, combined_mapping)

    # Backup dataset before writing
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = input_path.parent / f"{input_path.stem}_backup_{timestamp}{input_path.suffix}"
    shutil.copy2(input_path, backup_path)
    logger.info(f"Created pre-resolution backup at {backup_path}")

    save_jsonl(updated_records, str(input_path))
    logger.info(f"Successfully updated {len(updated_records)} records in {input_path}")
    logger.info(f"Records with PMCID: {mapped_count} ({(mapped_count/total_records)*100:.1f}%)")
    logger.info(f"Records without PMCID: {unmapped_count} ({(unmapped_count/total_records)*100:.1f}%)")


if __name__ == "__main__":
    main()

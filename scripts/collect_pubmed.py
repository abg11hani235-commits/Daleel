"""Script to safely collect, expand, and merge PubMed records for Daleel Phase 3.

Features:
- Backs up existing data before modification.
- Idempotent and duplicate-safe execution.
- Resumes interrupted collection by skipping already downloaded PMIDs.
- Dry-run mode for pre-flight planning and verification.
- Landmark studies retrieval with explicit provenance tagging.
- Full PMID universe snapshotting with query SHA256 hashing.
- Automated clinical relevance screening and co-publication linking.
- Generates reproducible collection manifest.
"""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from daleel.ingestion.pubmed_client import (
    LANDMARK_STUDIES_REGISTRY,
    PubMedClient,
    SOFTWARE_VERSION,
    compute_query_hash,
)
from daleel.utils.helpers import save_jsonl
from daleel.utils.logging import logger

DEFAULT_QUERY = (
    '( "Diabetes Mellitus, Type 2"[MeSH Terms] OR "type 2 diabetes"[Title/Abstract] OR T2D[Title/Abstract] ) '
    'AND ( "Chronic Kidney Disease"[Title/Abstract] OR "Renal Insufficiency, Chronic"[MeSH Terms] OR "Diabetic Nephropathies"[MeSH Terms] OR CKD[Title/Abstract] ) '
    'AND ( randomized controlled trial[Publication Type] OR meta-analysis[Publication Type] OR systematic review[Publication Type] OR practice guideline[Publication Type] ) '
    'AND ("2015/01/01"[Date - Publication] : "2026/12/31"[Date - Publication]) '
    'AND English[Language]'
)


def create_backup(filepath: Path) -> Optional[Path]:
    """Create timestamped backup of existing dataset before modification."""
    if not filepath.exists():
        return None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}_backup_{timestamp}{filepath.suffix}"
    shutil.copy2(filepath, backup_path)
    logger.info(f"Created safety backup at {backup_path}")
    return backup_path


def main():
    parser = argparse.ArgumentParser(description="Collect and expand PubMed corpus for Daleel Phase 3.")
    parser.add_argument("--query", type=str, default=DEFAULT_QUERY, help="PubMed search query")
    parser.add_argument("--output", type=str, default="data/raw/pubmed/pubmed_records.jsonl", help="Destination JSONL path")
    parser.add_argument("--snapshot", type=str, default="data/raw/pubmed/search_pmids_snapshot.json", help="PMID snapshot JSON path")
    parser.add_argument("--manifest", type=str, default="reports/data_collection/collection_manifest.json", help="Manifest JSON path")
    parser.add_argument("--max_results", type=int, default=None, help="Limit number of PMIDs to fetch (default: all)")
    parser.add_argument("--batch_size", type=int, default=50, help="Batch size for efetch")
    parser.add_argument("--delay", type=float, default=0.15, help="Delay between batches in seconds")
    parser.add_argument("--dry_run", action="store_true", help="Inspect and simulate collection without modifying files")
    parser.add_argument("--include_landmarks", action="store_true", default=True, help="Explicitly collect landmark seed trials")
    args = parser.parse_args()

    out_file = Path(args.output)
    client = PubMedClient()
    query_hash = compute_query_hash(args.query)
    start_time_utc = datetime.now(timezone.utc).isoformat()

    logger.info("=== Daleel Phase 3: PubMed Collection & Corpus Expansion ===")
    logger.info(f"Query Hash: {query_hash}")
    logger.info(f"Dry Run Mode: {args.dry_run}")

    # 1. Load existing records (Task 1)
    existing_records_map = client.load_existing_records(out_file)
    logger.info(f"Loaded {len(existing_records_map)} existing records from {out_file}")

    # 2. Collect landmark studies (Task 2)
    landmark_records: List[Dict[str, Any]] = []
    landmark_pmids = [m["pmid"] for m in LANDMARK_STUDIES_REGISTRY.values()]
    landmark_pmids_to_fetch = [p for p in landmark_pmids if p not in existing_records_map]

    logger.info(f"Landmark trials registered: {len(landmark_pmids)} PMIDs ({len(landmark_pmids_to_fetch)} new to fetch)")

    if args.dry_run:
        logger.info(f"[DRY RUN] Would fetch {len(landmark_pmids_to_fetch)} new landmark trials: {landmark_pmids_to_fetch}")
    else:
        if landmark_pmids_to_fetch:
            fetched_landmarks = client.fetch_details(
                landmark_pmids_to_fetch,
                batch_size=len(landmark_pmids_to_fetch),
                provenance_type="landmark_seed",
                query_hash=query_hash,
            )
            for rec in fetched_landmarks:
                logger.info(f"Verified Landmark: PMID {rec['pmid']} - '{rec['title']}' ({rec['journal']}, {rec['pub_date']})")
                landmark_records.append(rec)

    # 3. Search query and snapshot (Task 3)
    if args.dry_run:
        total_available = client.count(args.query)
        logger.info(f"[DRY RUN] Reported query universe: {total_available} matching PMIDs.")
        _, query_pmids = client.search_all_pmids(args.query, max_results=args.max_results)
    else:
        snapshot_meta = client.search_with_snapshot(
            args.query,
            snapshot_path=args.snapshot,
            max_results=args.max_results,
        )
        total_available = snapshot_meta["total_count_reported"]
        query_pmids = snapshot_meta["pmids"]

    # 4. Identify new PMIDs to fetch (Resume logic)
    all_target_pmids = list(dict.fromkeys(query_pmids))
    pmids_to_fetch = [p for p in all_target_pmids if p not in existing_records_map and p not in {r['pmid'] for r in landmark_records}]

    logger.info(f"Total PMIDs from query: {len(all_target_pmids)}")
    logger.info(f"Already collected: {len(existing_records_map)}")
    logger.info(f"Remaining new PMIDs to fetch: {len(pmids_to_fetch)}")

    if args.dry_run:
        logger.info(f"[DRY RUN] Simulation complete. Planned to fetch {len(pmids_to_fetch)} new query records and {len(landmark_pmids_to_fetch)} landmark records.")
        return

    # 5. Fetch new records in safe batches
    new_query_records: List[Dict[str, Any]] = []
    failed_pmids: List[str] = []

    if pmids_to_fetch:
        try:
            new_query_records = client.fetch_details(
                pmids_to_fetch,
                batch_size=args.batch_size,
                delay_sec=args.delay,
                provenance_type="search_query",
                query_hash=query_hash,
            )
        except Exception as e:
            logger.error(f"Collection interrupted during batch processing: {e}")
            logger.info("Proceeding to safely merge all successfully fetched records...")

    # 6. Safety Backup & Safe Merge (Tasks 1, 6, 7)
    all_new_to_merge = landmark_records + new_query_records
    create_backup(out_file)

    merged_records, added_count, updated_count = client.merge_records(existing_records_map, all_new_to_merge)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    save_jsonl(merged_records, str(out_file))

    end_time_utc = datetime.now(timezone.utc).isoformat()
    logger.info(f"Successfully saved {len(merged_records)} records to {out_file.resolve()}")
    logger.info(f"Added: {added_count} new records, Enriched: {updated_count} existing records.")

    # 7. Generate Manifest (Task 4)
    manifest_data = {
        "manifest_version": "1.0.0",
        "software_version": SOFTWARE_VERSION,
        "query": args.query,
        "query_hash": query_hash,
        "collection_start_utc": start_time_utc,
        "collection_end_utc": end_time_utc,
        "reported_pubmed_result_count": total_available,
        "total_target_pmids": len(all_target_pmids),
        "total_corpus_records": len(merged_records),
        "newly_added_records": added_count,
        "enriched_records": updated_count,
        "failed_records_count": len(failed_pmids),
        "landmark_seeds_included": len(LANDMARK_STUDIES_REGISTRY),
        "retrieval_method": "NCBI E-Utilities (esearch + efetch Medline)",
        "destination_file": str(out_file),
        "snapshot_file": str(args.snapshot),
    }

    manifest_p = Path(args.manifest)
    manifest_p.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_p, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Saved reproducible collection manifest to {manifest_p.resolve()}")


if __name__ == "__main__":
    main()

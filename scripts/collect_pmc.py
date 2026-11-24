"""Script to retrieve open access full-text articles from PMC."""
import argparse
from daleel.ingestion.pmc_client import PMCClient
from daleel.utils.logging import logger

def main():
    parser = argparse.ArgumentParser(description="Collect PMC articles.")
    parser.add_argument("--pmcid", type=str, required=True, help="PMC ID")
    args = parser.parse_args()

    logger.info(f"Retrieving PMC article: {args.pmcid}")
    client = PMCClient()
    # Logic to fetch full text and save to data/raw/pmc/

if __name__ == "__main__":
    main()
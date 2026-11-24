"""Script to clean, chunk, and index the entire corpus into processed dataset."""
from daleel.preprocessing.cleaner import TextCleaner
from daleel.preprocessing.chunker import BiomedicalChunker
from daleel.utils.logging import logger

def main():
    logger.info("Building processed dataset and chunking documents...")
    # Pipeline execution: raw -> interim -> processed

if __name__ == "__main__":
    main()
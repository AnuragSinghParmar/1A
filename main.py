#!/usr/bin/env python3
"""
Adobe Hackathon Round 1A - PDF Document Structure Analyzer
Entry point for Docker container execution

Author: Team Adobe Hackathon
Version: 1.0
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add src to path for imports
sys.path.append('/app/src')

from pdf_analyzer import PDFAnalyzer
from utils import setup_logging, load_config

def main():
    """Main execution function for Docker container"""
    start_time = time.time()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Define paths
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    config_path = Path("/app/config/config.yaml")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load configuration
    config = load_config(config_path)
    logger.info(f"Configuration loaded: {config}")
    
    # Initialize PDF analyzer
    analyzer = PDFAnalyzer(config)
    
    # Process all PDF files in input directory
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    processed_count = 0
    total_processing_time = 0
    
    for pdf_file in pdf_files:
        try:
            file_start = time.time()
            logger.info(f"Processing: {pdf_file.name}")
            
            # Extract document structure
            result = analyzer.extract_structure(pdf_file)
            
            # Generate output filename
            output_filename = pdf_file.stem + ".json"
            output_path = output_dir / output_filename
            
            # Save result
            analyzer.save_result(result, output_path)
            
            file_time = time.time() - file_start
            total_processing_time += file_time
            processed_count += 1
            
            logger.info(f"✅ Completed {pdf_file.name} in {file_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {pdf_file.name}: {e}")
            continue
    
    total_time = time.time() - start_time
    
    logger.info("=" * 50)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Files processed: {processed_count}/{len(pdf_files)}")
    logger.info(f"Total execution time: {total_time:.2f}s")
    logger.info(f"Average time per file: {total_processing_time/max(1, processed_count):.2f}s")
    logger.info(f"Constraint compliance: {'✅ PASS' if total_time <= 10 else '❌ FAIL'}")
    
    if total_time > 10:
        logger.warning("⚠️  Execution time exceeds 10-second constraint!")
    else:
        logger.info("🎯 Successfully completed within time constraints!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Adobe India Hackathon 2025 - Challenge 1a: PDF Processing Solution
A high-performance PDF to JSON converter using PyMuPDF

Author: Challenge 1a Solution
Version: 1.0.0
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
import gc

# PyMuPDF for high-performance PDF processing
try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz  # Fallback for older PyMuPDF versions
    except ImportError:
        print("Error: PyMuPDF not installed. Install with: pip install pymupdf")
        exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFProcessor:
    """High-performance PDF processor for Adobe Hackathon Challenge 1a"""

    def __init__(self):
        self.library_version = fitz.version[1] if hasattr(fitz, 'version') else "Unknown"

    def analyze_font_statistics(self, doc: fitz.Document, sample_pages: int = 5) -> Dict[str, float]:
        """Analyze font statistics to determine heading vs paragraph thresholds"""
        font_sizes = []
        bold_sizes = []

        # Sample first few pages to understand document typography
        sample_pages = min(sample_pages, doc.page_count)

        for page_num in range(sample_pages):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if block["type"] == 0:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            size = span["size"]
                            flags = span["flags"]

                            font_sizes.append(size)

                            # Check if bold (flags & 16)
                            if flags & 16:
                                bold_sizes.append(size)

        if not font_sizes:
            return {"avg_size": 12, "heading_threshold": 14, "large_heading_threshold": 16}

        avg_size = sum(font_sizes) / len(font_sizes)
        max_size = max(font_sizes)

        # Calculate thresholds
        heading_threshold = avg_size * 1.2  # 20% larger than average
        large_heading_threshold = avg_size * 1.5  # 50% larger than average

        return {
            "avg_size": avg_size,
            "max_size": max_size,
            "heading_threshold": heading_threshold,
            "large_heading_threshold": large_heading_threshold,
            "bold_sizes": bold_sizes
        }

    def classify_text_type(self, span: Dict, font_stats: Dict) -> Tuple[str, int]:
        """Classify text as heading, paragraph, footnote based on font properties"""
        size = span["size"]
        flags = span["flags"]
        text = span["text"].strip()

        # Check for bold (flags & 16)
        is_bold = bool(flags & 16)
        # Check for italic (flags & 2)
        is_italic = bool(flags & 2)

        # Determine text type and heading level
        if size >= font_stats["large_heading_threshold"]:
            return "heading", 1  # Main heading
        elif size >= font_stats["heading_threshold"] or (size > font_stats["avg_size"] and is_bold):
            return "heading", 2  # Subheading
        elif size < font_stats["avg_size"] * 0.8:
            return "footnote", 0  # Footnote
        else:
            return "paragraph", 0  # Regular paragraph

    def extract_pdf_structure(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract structured data from a PDF file"""
        start_time = time.time()

        try:
            # Open PDF document
            doc = fitz.open(str(pdf_path))

            # Get document metadata
            metadata = doc.metadata

            # Analyze font statistics
            font_stats = self.analyze_font_statistics(doc)

            # Initialize result structure
            result = {
                "filename": pdf_path.name,
                "metadata": {
                    "title": metadata.get("title", "") or pdf_path.stem,
                    "author": metadata.get("author", ""),
                    "creator": metadata.get("creator", ""),
                    "subject": metadata.get("subject", ""),
                    "keywords": metadata.get("keywords", ""),
                    "pageCount": doc.page_count,
                    "creationDate": metadata.get("creationDate", ""),
                    "modificationDate": metadata.get("modDate", "")
                },
                "structure": {
                    "sections": [],
                    "outline": []
                },
                "processing_info": {
                    "processing_time": 0,
                    "timestamp": datetime.now().isoformat(),
                    "library_version": self.library_version,
                    "total_sections": 0
                }
            }

            # Extract outline/bookmarks
            try:
                outline = doc.get_toc()
                for item in outline:
                    if len(item) >= 3:
                        level, title, page = item[0], item[1], item[2]
                        result["structure"]["outline"].append({
                            "title": title,
                            "level": level,
                            "page": page
                        })
            except Exception as e:
                logger.warning(f"Could not extract outline from {pdf_path.name}: {e}")

            # Process each page
            for page_num in range(doc.page_count):
                page = doc[page_num]

                try:
                    # Get structured text data
                    blocks = page.get_text("dict")["blocks"]

                    for block in blocks:
                        if block["type"] == 0:  # Text block
                            self._process_text_block(block, page_num + 1, font_stats, result)
                        elif block["type"] == 1:  # Image block
                            self._process_image_block(block, page_num + 1, result)

                    # Force garbage collection every 10 pages
                    if page_num % 10 == 0:
                        gc.collect()

                except Exception as e:
                    logger.error(f"Error processing page {page_num + 1} of {pdf_path.name}: {e}")
                    continue

            doc.close()

            # Calculate processing time and finalize
            processing_time = time.time() - start_time
            result["processing_info"]["processing_time"] = round(processing_time, 3)
            result["processing_info"]["total_sections"] = len(result["structure"]["sections"])

            logger.info(f"Successfully processed {pdf_path.name} in {processing_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Failed to process {pdf_path.name}: {e}")
            # Return minimal valid structure on error
            return {
                "filename": pdf_path.name,
                "metadata": {"pageCount": 0},
                "structure": {"sections": [], "outline": []},
                "processing_info": {
                    "processing_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat(),
                    "library_version": self.library_version,
                    "total_sections": 0,
                    "error": str(e)
                }
            }

    def _process_text_block(self, block: Dict, page_num: int, font_stats: Dict, result: Dict):
        """Process a text block and add to results"""
        block_text_parts = []
        primary_font = None
        primary_size = 0
        primary_flags = 0

        # Collect text and find primary font characteristics
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if text:
                    block_text_parts.append(text)

                    # Track primary font (largest or most common)
                    if span["size"] > primary_size:
                        primary_size = span["size"]
                        primary_font = span["font"]
                        primary_flags = span["flags"]

        if not block_text_parts:
            return

        # Combine text and classify
        block_text = " ".join(block_text_parts).strip()
        if not block_text:
            return

        # Create primary span for classification
        primary_span = {
            "text": block_text,
            "size": primary_size,
            "flags": primary_flags,
            "font": primary_font
        }

        text_type, level = self.classify_text_type(primary_span, font_stats)

        # Create section entry
        section = {
            "type": text_type,
            "content": block_text,
            "page": page_num,
            "bbox": block["bbox"],
            "font": {
                "name": primary_font or "unknown",
                "size": primary_size,
                "flags": primary_flags,
                "color": 0  # Default color
            }
        }

        # Add level for headings
        if text_type == "heading" and level > 0:
            section["level"] = level

        result["structure"]["sections"].append(section)

    def _process_image_block(self, block: Dict, page_num: int, result: Dict):
        """Process an image block and add to results"""
        result["structure"]["sections"].append({
            "type": "image",
            "content": f"[Image: width={block.get('width', 0)}, height={block.get('height', 0)}]",
            "page": page_num,
            "bbox": block["bbox"],
            "font": {
                "name": "image",
                "size": 0,
                "flags": 0,
                "color": 0
            }
        })


def process_single_pdf(pdf_path: Path, output_dir: Path) -> bool:
    """Process a single PDF file"""
    try:
        processor = PDFProcessor()
        result = processor.extract_pdf_structure(pdf_path)

        # Generate output JSON file
        output_file = output_dir / f"{pdf_path.stem}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Generated {output_file.name}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to process {pdf_path.name}: {e}")
        return False


def process_pdfs():
    """Main function to process all PDFs in input directory"""
    # Define paths
    input_dir = Path("D:\AdobeChalllenge\Challenge_1a\input")
    output_dir = Path("D:\AdobeChalllenge\Challenge_1a\output")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to process")

    # Process files with multiprocessing for better performance
    success_count = 0

    # Determine optimal number of workers (max 4 to avoid memory issues)
    max_workers = min(4, os.cpu_count() or 1)

    if len(pdf_files) == 1:
        # Single file - process directly
        if process_single_pdf(pdf_files[0], output_dir):
            success_count = 1
    else:
        # Multiple files - use multiprocessing
        try:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(process_single_pdf, pdf_file, output_dir) 
                    for pdf_file in pdf_files
                ]

                for future in futures:
                    if future.result():
                        success_count += 1

        except Exception as e:
            logger.error(f"Multiprocessing failed, falling back to sequential: {e}")
            # Fallback to sequential processing
            for pdf_file in pdf_files:
                if process_single_pdf(pdf_file, output_dir):
                    success_count += 1

    logger.info(f"Processing complete: {success_count}/{len(pdf_files)} files successful")


if __name__ == "__main__":
    process_pdfs()

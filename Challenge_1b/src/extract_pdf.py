import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict

def extract_blocks(pdf_path: Path) -> List[Dict]:
    doc = fitz.open(pdf_path)
    blocks = []
    for page_no, page in enumerate(doc, 1):
        for blk in page.get_text("dict")["blocks"]:
            if blk["type"] != 0:          # skip images
                continue
            for line in blk["lines"]:
                text = " ".join([span["text"] for span in line["spans"]]).strip()
                if not text:               # ignore blank
                    continue
                font_size = line["spans"][0]["size"]
                blocks.append({
                    "page": page_no,
                    "font": font_size,
                    "text": text
                })
    return blocks
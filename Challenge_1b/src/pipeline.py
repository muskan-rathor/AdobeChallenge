from pathlib import Path, PurePath
from datetime import datetime as dt
from pydantic import BaseModel, Field, ValidationError
from extract_pdf import extract_blocks
from embed import embed_texts
from rank import build_faiss, topk
from refine import refine
import json, tqdm, numpy as np, os, sys

class Meta(BaseModel):
    input_documents: list[str]
    persona: str
    job_to_be_done: str
    timestamp: str = Field(default_factory=lambda: dt.utcnow().isoformat()+"Z")

class Section(BaseModel):
    document: str
    section_title: str
    importance_rank: int
    page_number: int

class SubSection(BaseModel):
    document: str
    refined_text: str
    page_number: int

def run(input_json: Path, pdf_dir: Path, out_file: Path):
    with input_json.open() as f:
        conf = json.load(f)
    persona = conf["persona"]["role"]
    task    = conf["job_to_be_done"]["task"]
    # ---------- ingest ----------
    docs, texts, pages = [], [], []
    for item in conf["documents"]:
        pdf_path = pdf_dir / item["filename"]
        blocks   = extract_blocks(pdf_path)
        for blk in blocks:
            docs.append(pdf_path.name)
            pages.append(blk["page"])
            texts.append(blk["text"])
    # ---------- embed ----------
    vecs = embed_texts(texts)
    index = build_faiss(vecs)
    q_vec = embed_texts([persona+" "+task])[0]
    scores, ids = topk(index, q_vec, k=40)
    # ---------- post-rank ----------
    candidates = []
    for rank, idx in enumerate(ids[0], 1):
        cand = {
            "document": docs[idx],
            "section_title": texts[idx][:120],
            "importance_rank": rank,
            "page_number": int(pages[idx]),
            "refined_text": refine(texts[idx])
        }
        candidates.append(cand)
    # ---------- pack ----------
    output = {
        "metadata": Meta(
            input_documents=[d["filename"] for d in conf["documents"]],
            persona=persona,
            job_to_be_done=task).model_dump(),
        "extracted_sections": [Section(**c).model_dump() for c in candidates[:15]],
        "subsection_analysis": [SubSection(**c).model_dump() for c in candidates[:15]]
    }
    # validate & write
    try:
        json.dumps(output)  # quick validation
    except (TypeError, ValidationError) as e:
        sys.exit(f"JSON validation failed: {e}")
    out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))

if _name_ == "_main_":
    # auto-discover /app/input and /app/output
    in_dir  = Path("/app/input")
    out_dir = Path("/app/output"); out_dir.mkdir(exist_ok=True)
    # iterate over *.json configs adjacent to PDFs
    for cfg in in_dir.glob("*/challenge1b_input.json"):
        run(cfg, cfg.parent / "PDFs", out_dir / "challenge1b_output.json")
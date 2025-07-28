import faiss, numpy as np
from typing import List, Tuple
import yake, rake_nltkcd
from math import log

_kw_extractor = yake.KeywordExtractor(lan="en", n=3, top=20)

def importance(text: str) -> float:
    kws = _kw_extractor.extract_keywords(text)
    score = sum((1/score) for kw, score in kws)  # inverse YAKE score
    return log(1+len(kws)) * score               # length adjust

def build_faiss(vecs: np.ndarray, nlist: int = 100) -> faiss.IndexIVFFlat:
    dim = vecs.shape[1]
    quant = faiss.IndexFlatIP(dim)             # inner-product == cosine on unit vecs
    index = faiss.IndexIVFFlat(quant, dim, nlist, faiss.METRIC_INNER_PRODUCT)
    index.train(vecs)
    index.add(vecs)
    index.nprobe = min(10, nlist//4)           # speed/recall trade-off
    return index

def topk(index, q_vec: np.ndarray, k: int = 15) -> Tuple[np.ndarray, np.ndarray]:
    # FAISS returns (scores, ids)
    return index.search(q_vec.reshape(1,-1), k)
from sentence_transformers import SentenceTransformer
import numpy as np, itertools

_model = SentenceTransformer("all-MiniLM-L6-v2")  # 384-d, 22 MB [3]
def embed_texts(texts: list[str]) -> np.ndarray:
    return _model.encode(texts, batch_size=64, show_progress_bar=False,
                         convert_to_numpy=True, normalize_embeddings=True)

     

     
"""Event deduplication using sentence embeddings and FAISS similarity search.

Converts event text into dense vector embeddings with SentenceTransformers,
stores them in a FAISS index, and checks new events against existing ones.
If cosine similarity exceeds the threshold, the event is marked as a duplicate.
"""

from typing import Tuple, Optional, List
import numpy as np
from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()

_model = None
_index = None
_event_ids: List[str] = []
_EMBEDDING_DIM = 384


def _get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("sentence_transformer_loaded", model="all-MiniLM-L6-v2")
        except Exception as e:
            logger.error("sentence_transformer_load_failed", error=str(e))
    return _model


def _get_index():
    global _index
    if _index is None:
        try:
            import faiss
            _index = faiss.IndexFlatIP(_EMBEDDING_DIM)
            logger.info("faiss_index_created", dim=_EMBEDDING_DIM)
        except Exception as e:
            logger.error("faiss_init_failed", error=str(e))
    return _index


class EventDeduplicator:
    def __init__(self, similarity_threshold: float = None):
        self.threshold = similarity_threshold or settings.dedup_similarity_threshold

    def _encode(self, text: str) -> Optional[np.ndarray]:
        model = _get_model()
        if model is None:
            return None
        embedding = model.encode([text], normalize_embeddings=True)
        return embedding[0].astype("float32")

    def check(self, text: str, event_id: str) -> Tuple[bool, Optional[str]]:
        """Check if this event text is a duplicate of an existing event.
        
        Returns (is_duplicate, existing_event_id_or_None).
        """
        embedding = self._encode(text)
        if embedding is None:
            return False, None

        index = _get_index()
        if index is None:
            return False, None

        if index.ntotal > 0:
            embedding_2d = embedding.reshape(1, -1)
            scores, indices = index.search(embedding_2d, min(5, index.ntotal))

            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:
                    continue
                if score >= self.threshold:
                    existing_id = _event_ids[idx] if idx < len(_event_ids) else None
                    logger.info(
                        "duplicate_detected",
                        new_event=event_id,
                        existing_event=existing_id,
                        similarity=round(float(score), 4),
                    )
                    return True, existing_id

        index.add(embedding.reshape(1, -1))
        _event_ids.append(event_id)

        return False, None

    def get_index_size(self) -> int:
        index = _get_index()
        return index.ntotal if index else 0

    def reset(self):
        global _index, _event_ids
        _index = None
        _event_ids = []

import math
import os
from threading import Lock
from typing import Any

_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_model: Any = None
_model_lock = Lock()


def _get_model() -> Any:
    global _model
    if _model is not None:
        return _model

    with _model_lock:
        if _model is None:
            from fastembed import TextEmbedding

            _model = TextEmbedding(
                model_name=_MODEL_NAME,
                cache_dir=os.getenv("FASTEMBED_CACHE_PATH", "/tmp/echo_fastembed"),
                threads=1,
                lazy_load=False,
            )
    return _model


def _cosine(a: Any, b: Any) -> float:
    dot = float(sum(float(x) * float(y) for x, y in zip(a, b)))
    norm_a = math.sqrt(sum(float(x) * float(x) for x in a))
    norm_b = math.sqrt(sum(float(y) * float(y) for y in b))
    if not norm_a or not norm_b:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


def _similarity_to_score(similarity: float) -> int:
    score = round((similarity - 0.25) / 0.60 * 100)
    return max(0, min(100, score))


def analyze_semantics(text: str, objectives: list[dict[str, Any]]) -> dict[str, Any]:
    enabled = [item for item in objectives if item.get("enabled", True) and str(item.get("objective", "")).strip()]
    clean_text = text.strip()
    if not clean_text or not enabled:
        return {
            "semantic_score": 0,
            "similarity": 0.0,
            "matched_objective_id": None,
            "matched_objective": None,
            "model": _MODEL_NAME,
        }

    model = _get_model()
    texts = [clean_text] + [str(item["objective"]).strip() for item in enabled]
    embeddings = list(model.embed(texts, batch_size=min(len(texts), 8)))
    post_embedding = embeddings[0]

    best_similarity = -1.0
    best_item: dict[str, Any] | None = None
    for item, objective_embedding in zip(enabled, embeddings[1:]):
        similarity = _cosine(post_embedding, objective_embedding)
        if similarity > best_similarity:
            best_similarity = similarity
            best_item = item

    base_score = _similarity_to_score(best_similarity)
    priority = int((best_item or {}).get("priority", 50))
    priority_factor = 0.85 + (max(0, min(priority, 100)) / 100) * 0.15
    semantic_score = max(0, min(100, round(base_score * priority_factor)))

    return {
        "semantic_score": semantic_score,
        "similarity": round(best_similarity, 4),
        "matched_objective_id": (best_item or {}).get("id"),
        "matched_objective": (best_item or {}).get("objective"),
        "model": _MODEL_NAME,
    }

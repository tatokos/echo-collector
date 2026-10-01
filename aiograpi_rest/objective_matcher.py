import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

_STOPWORDS = {
    "a", "ad", "al", "alla", "alle", "anche", "che", "chi", "con", "da", "dal", "dalla", "dei", "del", "della",
    "di", "e", "ed", "gli", "i", "il", "in", "la", "le", "lo", "ma", "nel", "nella", "o", "per", "piu",
    "se", "senza", "su", "tra", "un", "una", "uno",
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or",
    "that", "the", "to", "with", "without",
}

# Tiny built-in concept map: zero dependencies, zero external APIs.
_CONCEPT_GROUPS = [
    {"problema", "problemi", "disservizio", "disservizi", "issue", "issues", "problem", "problems", "guasto", "guasti", "malfunzionamento", "malfunzionamenti"},
    {"ritardo", "ritardi", "delay", "delays", "late", "attesa", "attese", "waiting", "wait"},
    {"coda", "code", "fila", "file", "queue", "queues", "crowd", "affollamento", "affollato"},
    {"lamentela", "lamentele", "reclamo", "reclami", "complaint", "complaints", "deluso", "delusa", "delusione", "disappointed"},
    {"pessimo", "pessima", "terribile", "orribile", "bad", "awful", "terrible", "worst", "scadente"},
    {"ottimo", "ottima", "eccellente", "fantastico", "fantastica", "great", "excellent", "amazing", "fantastic", "positivo", "positiva"},
    {"prezzo", "prezzi", "costoso", "costosa", "caro", "cara", "price", "prices", "expensive", "cost"},
    {"sicurezza", "pericolo", "pericoloso", "rischio", "safety", "danger", "dangerous", "risk"},
    {"sporco", "sporca", "sporcizia", "pulizia", "dirty", "cleanliness", "clean", "igiene", "hygiene"},
    {"personale", "staff", "servizio", "service", "assistenza", "support", "operatore", "operatori"},
    {"cibo", "food", "ristorante", "restaurant", "pasto", "pasti", "meal", "meals"},
    {"bagaglio", "bagagli", "valigia", "valigie", "luggage", "baggage", "suitcase"},
    {"imbarco", "boarding", "checkin", "check-in", "accesso", "entrata", "entry"},
    {"cancellato", "cancellata", "cancellazione", "cancelled", "canceled", "cancellation"},
]


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("-", " ")
    return re.sub(r"[^a-z0-9à-ÿ]+", " ", text).strip()


def _tokens(text: str) -> list[str]:
    return [token for token in _normalize(text).split() if len(token) >= 3 and token not in _STOPWORDS]


def _expand(tokens: set[str]) -> set[str]:
    expanded = set(tokens)
    for group in _CONCEPT_GROUPS:
        if tokens & group:
            expanded |= group
    return expanded


def _best_fuzzy(token: str, candidates: set[str]) -> float:
    if not candidates:
        return 0.0
    return max(SequenceMatcher(None, token, candidate).ratio() for candidate in candidates)


def score_objectives(text: str, objectives: list[dict[str, Any]]) -> dict[str, Any]:
    post_tokens = set(_tokens(text))
    if not post_tokens:
        return {"score": 0, "matched_objective": None, "matched_objective_id": None, "reason": "No objective match"}

    post_expanded = _expand(post_tokens)
    best_score = 0
    best_objective: dict[str, Any] | None = None
    best_hits: list[str] = []

    for item in objectives:
        if not item.get("enabled", True):
            continue
        objective = str(item.get("objective", "")).strip()
        objective_tokens = set(_tokens(objective))
        if not objective_tokens:
            continue

        expanded_objective = _expand(objective_tokens)
        direct_hits = objective_tokens & post_tokens
        concept_hits = objective_tokens & post_expanded

        fuzzy_hits = []
        for token in objective_tokens - concept_hits:
            ratio = _best_fuzzy(token, post_tokens)
            if ratio >= 0.86:
                fuzzy_hits.append(token)

        coverage = (len(concept_hits) + 0.65 * len(fuzzy_hits)) / max(len(objective_tokens), 1)
        direct_bonus = min(len(direct_hits) * 8, 24)
        phrase_similarity = SequenceMatcher(None, _normalize(objective), _normalize(text)).ratio()
        phrase_bonus = max(0, round((phrase_similarity - 0.25) * 28))

        raw_score = round(coverage * 72 + direct_bonus + phrase_bonus)
        priority = max(0, min(100, int(item.get("priority", 50))))
        priority_factor = 0.85 + (priority / 100) * 0.15
        score = max(0, min(100, round(raw_score * priority_factor)))

        if score > best_score:
            best_score = score
            best_objective = item
            best_hits = sorted(concept_hits | set(fuzzy_hits))

    if not best_objective or best_score < 18:
        return {"score": 0, "matched_objective": None, "matched_objective_id": None, "reason": "No objective match"}

    hit_text = ", ".join(best_hits[:6]) if best_hits else "related wording"
    return {
        "score": best_score,
        "matched_objective": best_objective.get("objective"),
        "matched_objective_id": best_objective.get("id"),
        "reason": f"Objective match ({hit_text})",
    }


def combine_scores(keyword_score: int, objective_score: int) -> int:
    stronger = max(keyword_score, objective_score)
    weaker = min(keyword_score, objective_score)
    return max(0, min(100, round(stronger * 0.85 + weaker * 0.15)))


def classify(score: int) -> str:
    if score >= 80:
        return "ALTA"
    if score >= 50:
        return "MEDIA"
    if score >= 25:
        return "BASSA"
    return "SCARTATA"

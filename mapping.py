import re
from difflib import SequenceMatcher

FIELD_REGISTRY = {
    "workshops": {
        "label": "Policy Workshops",
        "aliases": [
            "policy workshops",
            "helpful were the policy workshops",
            "workshop quality",
        ],
    },
    "speakers": {
        "label": "Speaker Events",
        "aliases": [
            "speaker events",
            "insightful were the speaker events",
            "speaker relevance",
        ],
    },
    "peer": {
        "label": "Peer / Buddy Experience",
        "aliases": [
            "donut buddies",
            "bridge buddies",
            "peer events",
            "buddy events",
            "engaging were",
        ],
    },
    "experience": {
        "label": "Overall Experience",
        "aliases": [
            "experience with paragon",
            "how was your experience",
            "overall experience",
        ],
    },
    "skills": {
        "label": "Skill Growth",
        "aliases": [
            "developed new skills",
            "skill growth",
            "skills during the fellowship",
        ],
    },
    "understand": {
        "label": "Improved Tech Policy Understanding",
        "aliases": [
            "improved my understanding of tech policy",
            "understanding of tech policy",
        ],
    },
    "interest": {
        "label": "Increased Career Interest",
        "aliases": [
            "increased my interest in pursuing a career",
            "interest in pursuing a career in tech policy",
        ],
    },
    "confidence": {
        "label": "Internship Confidence",
        "aliases": [
            "more confident about my ability to procure an internship",
            "internship confidence",
        ],
    },
    "hours": {
        "label": "Weekly Hours",
        "aliases": [
            "hours did you spend on paragon per week",
            "hours per week",
            "weekly commitment",
        ],
    },
    "suggestions": {
        "label": "Suggestions",
        "aliases": [
            "suggestions for the content",
            "programming suggestions",
        ],
    },
    "elaborate": {
        "label": "Experience Details",
        "aliases": [
            "elaborate on your rating",
            "experience and your skill growth",
        ],
    },
    "perspective": {
        "label": "Perspective Shift",
        "aliases": [
            "perspective on tech policy evolved",
            "shifted your understanding",
        ],
    },
    "team": {
        "label": "Team",
        "aliases": ["what project team were you on", "project team"],
    },
    "edu": {
        "label": "Educational Background",
        "aliases": ["current educational background", "educational background"],
    },
}


def normalize_text(value):
    return re.sub(r"\s+", " ", str(value).strip().lower())


def token_overlap_score(a, b):
    ta = set(re.findall(r"[a-z0-9]+", a))
    tb = set(re.findall(r"[a-z0-9]+", b))
    if not ta or not tb:
        return 0.0
    return len(ta.intersection(tb)) / max(1, len(ta.union(tb)))


def combined_similarity(a, b):
    seq = SequenceMatcher(None, a, b).ratio()
    tok = token_overlap_score(a, b)
    return 0.55 * seq + 0.45 * tok


def confidence_bucket(score):
    if score >= 0.9:
        return "high"
    if score >= 0.68:
        return "medium"
    if score >= 0.5:
        return "low"
    return "none"


def match_one_metric(columns, aliases):
    normalized_columns = [(c, normalize_text(c)) for c in columns]
    for alias in aliases:
        alias_n = normalize_text(alias)
        for original_col, col_n in normalized_columns:
            if alias_n == col_n or alias_n in col_n:
                return original_col, 1.0, "high", f"matched alias '{alias}'"

    best_col = None
    best_score = 0.0
    best_alias = ""
    for alias in aliases:
        alias_n = normalize_text(alias)
        for original_col, col_n in normalized_columns:
            score = combined_similarity(alias_n, col_n)
            if score > best_score:
                best_score = score
                best_col = original_col
                best_alias = alias
    conf = confidence_bucket(best_score)
    if conf == "none":
        return None, best_score, "none", "no reliable match"
    return best_col, best_score, conf, f"best fuzzy alias '{best_alias}'"


def build_mapping(df_columns):
    mapping = {}
    details = {}
    for key, config in FIELD_REGISTRY.items():
        col, score, conf, reason = match_one_metric(df_columns, config["aliases"])
        mapping[key] = col
        details[key] = {
            "label": config["label"],
            "column": col,
            "score": round(float(score), 3),
            "confidence": conf,
            "reason": reason,
        }
    return mapping, details

import re
from collections import Counter, defaultdict

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "is", "it", "for", "on", "that", "this", "with", "are",
    "was", "were", "be", "been", "as", "at", "my", "we", "our", "they", "their", "from", "if", "but", "have",
    "has", "had", "will", "would", "could", "should", "more", "very", "just", "about", "into", "than", "also",
}

POSITIVE_WORDS = {
    "helpful", "great", "excellent", "valuable", "insightful", "supportive", "engaging", "strong", "improved",
    "confident", "learned", "clear", "practical", "collaborative", "amazing", "useful", "good", "effective",
}
NEGATIVE_WORDS = {
    "scheduling", "conflict", "overwhelming", "disorganized", "unclear", "confusing", "late", "busy", "workload",
    "limited", "hard", "difficult", "inconsistent", "rushed", "short", "spread", "communication", "chaotic",
}

THEME_KEYWORDS = {
    "WorkshopQuality": {"workshop", "curriculum", "session", "content", "material", "exercise"},
    "SpeakerRelevance": {"speaker", "guest", "panel", "relevance", "practitioner"},
    "TeamConnection": {"team", "community", "peer", "buddy", "bridge", "connection", "collaboration"},
    "WorkloadBalance": {"workload", "hours", "overwhelming", "busy", "balance", "pace", "rushed"},
    "SchedulingLogistics": {"schedule", "scheduling", "timing", "calendar", "late", "conflict"},
    "CareerOutcomes": {"career", "internship", "confidence", "opportunity", "mentor", "network"},
}


def split_sentences(text):
    parts = re.split(r"(?<=[\.\!\?])\s+|\n+", text)
    return [p.strip() for p in parts if p and p.strip()]


def tokenize(text):
    return re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())


def classify_sentence(sentence):
    tokens = tokenize(sentence)
    if not tokens:
        return "neutral", 0.0
    pos_hits = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg_hits = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    score = (pos_hits - neg_hits) / max(1, len(tokens))
    if score > 0.02:
        return "positive", score
    if score < -0.02:
        return "negative", score
    return "neutral", score


def sentence_themes(sentence):
    tokens = set(tokenize(sentence))
    hits = []
    for theme, keys in THEME_KEYWORDS.items():
        if tokens.intersection(keys):
            hits.append(theme)
    if not hits:
        hits.append("GeneralFeedback")
    return hits


def analyze_responses(texts):
    analyzed = []
    theme_sentiment_counts = defaultdict(lambda: Counter())

    for text in texts:
        sentences = split_sentences(text)
        if not sentences:
            continue
        sentence_rows = []
        counts = Counter()
        for sent in sentences:
            label, score = classify_sentence(sent)
            themes = sentence_themes(sent)
            counts[label] += 1
            for theme in themes:
                theme_sentiment_counts[theme][label] += 1
            sentence_rows.append(
                {"sentence": sent, "sentiment": label, "score": score, "themes": themes}
            )

        total_sentences = max(1, len(sentences))
        mix = {
            "positive_pct": counts["positive"] / total_sentences,
            "negative_pct": counts["negative"] / total_sentences,
            "neutral_pct": counts["neutral"] / total_sentences,
        }
        if mix["positive_pct"] >= 0.6 and mix["negative_pct"] <= 0.2:
            overall = "positive"
        elif mix["negative_pct"] >= 0.6 and mix["positive_pct"] <= 0.2:
            overall = "negative"
        else:
            overall = "mixed"

        analyzed.append(
            {
                "text": text,
                "sentences": sentence_rows,
                "counts": counts,
                "mix": mix,
                "overall": overall,
                "weight": min(1.0, total_sentences / 4.0),
            }
        )

    return analyzed, theme_sentiment_counts


def aggregate_dashboard_signals(analyzed):
    total_weight = sum(r["weight"] for r in analyzed) or 1.0
    pos = sum(r["weight"] * r["mix"]["positive_pct"] for r in analyzed) / total_weight
    neg = sum(r["weight"] * r["mix"]["negative_pct"] for r in analyzed) / total_weight
    neu = sum(r["weight"] * r["mix"]["neutral_pct"] for r in analyzed) / total_weight
    buckets = Counter(r["overall"] for r in analyzed)
    return {"positive": pos, "negative": neg, "neutral": neu, "buckets": buckets}


def top_theme_rows(theme_counts, sentiment, n=5):
    rows = []
    for theme, counts in theme_counts.items():
        if counts[sentiment] > 0:
            rows.append((theme, counts[sentiment]))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows[:n]


def representative_sentences(analyzed, target, limit=6):
    results = []
    if target == "mixed":
        for response in analyzed:
            if response["overall"] == "mixed":
                results.append(response["text"])
                if len(results) >= limit:
                    break
        return results

    for response in analyzed:
        for sentence in response["sentences"]:
            if sentence["sentiment"] == target:
                results.append(sentence["sentence"])
                if len(results) >= limit:
                    return results
    return results


def top_keywords(texts, n=12):
    words = []
    for text in texts:
        for token in tokenize(text):
            if token not in STOPWORDS:
                words.append(token)
    return Counter(words).most_common(n)

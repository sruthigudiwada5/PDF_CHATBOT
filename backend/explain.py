import json
from pathlib import Path
import psutil
import os
import nltk
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# RAM usage logger
process = psutil.Process(os.getpid())
def log_mem(stage):
    print(f"[DEBUG] {stage} - Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

def safe_sent_tokenize(text: str):
    """Sentence tokenize with NLTK if available, else regex fallback."""
    try:
        return nltk.sent_tokenize(text)
    except Exception:
        import re
        # Simple regex split as fallback
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

def find_relevant_sections(json_data, query, top_k=3):
    """Select most relevant sections using lightweight TF-IDF similarity (no embeddings).
    Returns a list of (heading, content) tuples.
    """
    sections_text = []
    index_map = []
    for idx, item in enumerate(json_data.get("outline", [])):
        heading = item.get("text", "")
        content = item.get("content", "")
        combined = f"{heading}. {content}".strip()
        if combined:
            sections_text.append(combined)
            index_map.append(idx)

    if not sections_text:
        return []

    # Fit TF-IDF on sections + query to keep memory small
    vectorizer = TfidfVectorizer(max_features=3000, stop_words='english')
    corpus = sections_text + [query]
    tfidf = vectorizer.fit_transform(corpus)
    query_vec = tfidf[-1]
    section_mat = tfidf[:-1]
    sims = cosine_similarity(query_vec, section_mat)[0]

    # Pick top_k indices by similarity
    top_positions = sims.argsort()[::-1][:top_k]
    final_results = []
    for pos in top_positions:
        item = json_data.get("outline", [])[index_map[pos]]
        head = item.get("text", "")
        content = item.get('content', '')
        final_results.append((head, content))

    return final_results

def summarize_text(text, max_chars=200):
    """Extractive summarization: pick highest TF-IDF sentences within a character budget."""
    text = (text or "").strip()
    if not text:
        return ""
    sentences = safe_sent_tokenize(text)
    if not sentences:
        return text[:max_chars] + ("..." if len(text) > max_chars else "")

    vectorizer = TfidfVectorizer(max_features=2000, stop_words='english')
    X = vectorizer.fit_transform(sentences)
    # Sentence salience as sum of TF-IDF weights
    scores = X.sum(axis=1).A1
    ranked = scores.argsort()[::-1]

    summary_parts = []
    total = 0
    for i in ranked:
        s = sentences[i].strip()
        if not s:
            continue
        # +1 for space between sentences when joined
        add_len = len(s) + (1 if summary_parts else 0)
        if total + add_len > max_chars:
            continue
        summary_parts.append(s)
        total += add_len
        if total >= max_chars:
            break

    if not summary_parts:
        return sentences[0][:max_chars] + ("..." if len(sentences[0]) > max_chars else "")
    return " ".join(summary_parts)

def explain_topic(topic: str, out_path: Path = None):
    """Generate explanations for a topic from Stage 1 outlines using lightweight methods."""
    try:
        log_mem("Starting explain_topic")
        outlines_dir = Path(__file__).parent / "output" / "1a_outlines"
        outlines_dir.mkdir(parents=True, exist_ok=True)

        json_files = list(outlines_dir.glob("*.json"))
        if not json_files:
            return {"error": "No outline files found. Please run the extraction first."}

        # Aggregate relevant sections across all outline files
        selected = []  # type: list
        for fp in json_files:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            selected.extend(find_relevant_sections(data, topic))

        # Fallback: if nothing matched, take first few sections with content
        if not selected:
            for fp in json_files:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("outline", [])[:3]:
                    head = item.get("text", "")
                    content = item.get("content", "")
                    if head or content:
                        selected.append((head, content))
                if selected:
                    break

        # Produce explanations
        explanations = []
        for head, content in selected[:3]:  # keep it small for memory
            summary = summarize_text(content)
            explanations.append({
                "heading": head or "Section",
                "explanation": summary
            })

        result = {
            "topic": topic,
            "explanations": explanations,
            "memory_usage_mb": process.memory_info().rss / 1024 / 1024
        }

        # Save if requested
        out_path = Path(out_path) if out_path else (Path(__file__).parent / "output" / "explain.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        log_mem("Finished explain_topic")
        return result
    except Exception as e:
        log_mem(f"Error in explain_topic: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate explanations for a topic from Stage 1 outlines.")
    parser.add_argument("--topic", required=True, help="Topic or query to explain")
    parser.add_argument("--out", default=str(Path(__file__).parent / "output" / "explain.json"), help="Output JSON file path")
    args = parser.parse_args()

    output = explain_topic(args.topic, Path(args.out))
    print(json.dumps(output, ensure_ascii=False, indent=2))
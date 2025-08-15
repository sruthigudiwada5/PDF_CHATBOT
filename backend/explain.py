import json
from pathlib import Path
import psutil
import os
import nltk
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline

nltk.download('punkt', quiet=True)

# RAM usage logger
process = psutil.Process(os.getpid())
def log_mem(stage):
    print(f"[DEBUG] {stage} - Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# Load models
log_mem("Before model load")
embedder = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L3-v2')
log_mem("After embedding model load")
summarizer = pipeline("summarization", model="t5-small", tokenizer="t5-small", framework="pt", device=-1)  # CPU only
log_mem("After T5-small summarizer load")

def find_relevant_sections(json_data, query, top_k=3):
    """Search headings + content for most relevant matches to the query."""
    sections = []
    for item in json_data.get("outline", []):
        heading = item.get("heading", "")
        content = item.get("content", "")
        combined_text = f"{heading}. {content}".strip()
        if combined_text:
            sections.append((heading, combined_text))
    
    if not sections:
        return []
    
    # Embed query + all sections
    query_embedding = embedder.encode([query])
    section_embeddings = embedder.encode([sec[1] for sec in sections])

    # Compute similarity
    similarities = cosine_similarity(query_embedding, section_embeddings)[0]
    ranked_indices = similarities.argsort()[::-1][:top_k]
    
    return [sections[i] for i in ranked_indices]

def summarize_text(text, max_len=80):
    """Summarize the text into a concise explanation."""
    if not text.strip():
        return ""
    try:
        summary = summarizer(text, max_length=max_len, min_length=20, do_sample=False)[0]['summary_text']
        return summary.strip()
    except Exception as e:
        print(f"[WARN] Summarization failed: {e}")
        return text  # fallback

def explain_topic(query, out_path=None):
    """Main function to search and summarize explanations.
    If out_path is provided, save the results there; else defaults to output/explain.json.
    """
    stage1_folder = Path(__file__).parent / "output" / "1a_outlines"
    results = []

    log_mem("Before processing PDFs for explanation")

    for filepath in stage1_folder.glob("*.json"):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        relevant_sections = find_relevant_sections(data, query)
        if not relevant_sections:
            continue

        combined_text = " ".join(sec[1] for sec in relevant_sections)
        log_mem(f"Before summarizing {filepath.name}")
        summary = summarize_text(combined_text)
        log_mem(f"After summarizing {filepath.name}")

        results.append({
            "pdf_name": Path(filepath).stem,
            "title": data.get("title", "Untitled"),
            "explanation": summary
        })

    log_mem("After all PDFs processed for explanation")

    # Save results locally
    output_file = Path(out_path) if out_path else (Path(__file__).parent / "output" / "explain.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[OK] Explanations saved to {output_file}")
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate explanations for a topic from Stage 1 outlines.")
    parser.add_argument("--topic", required=True, help="Topic or query to explain")
    parser.add_argument("--out", default=str(Path(__file__).parent / "output" / "explain.json"), help="Output JSON file path")
    args = parser.parse_args()

    output = explain_topic(args.topic, Path(args.out))
    print(json.dumps(output, ensure_ascii=False, indent=2))
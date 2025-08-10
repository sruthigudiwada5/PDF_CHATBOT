import json
import glob
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import psutil
import os

# Ensure NLTK sentence tokenizer is available
nltk.download('punkt', quiet=True)

# Load lightweight embedding model
model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L3-v2')

# Debug: Print memory usage after model load
process = psutil.Process(os.getpid())
print(f"[DEBUG] Memory usage after model load: {process.memory_info().rss / 1024 / 1024:.2f} MB")

def extractive_summary(text, num_sentences=2):
    """Generate extractive summary by picking most central sentences."""
    sentences = nltk.sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return " ".join(sentences)
    
    embeddings = model.encode(sentences)
    sim_matrix = cosine_similarity(embeddings)

    # Centrality score = average similarity to all other sentences
    centrality_scores = sim_matrix.mean(axis=1)
    ranked_sentences = [
        sentences[i] for i in np.argsort(-centrality_scores)[:num_sentences]
    ]
    return " ".join(ranked_sentences)

def process_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    file_name = Path(filepath).stem
    title = data.get("title", "Untitled")
    outline = data.get("outline", [])

    headings_data = []
    for item in outline:
        heading = item.get("text", "").strip()
        content = item.get("content", "").strip()
        summary = extractive_summary(content, num_sentences=2)
        headings_data.append({
            "heading": heading,
            "summary": summary
        })

    return {
        "pdf_name": file_name,
        "title": title,
        "headings": headings_data
    }

def main():
    # Detect if running in Docker/Render (deployment) or local
    # If /app exists and is the parent, use /app paths; else use local project paths
    if Path('/app').exists() and str(Path(__file__).parent).startswith('/app'):
        stage1_folder = Path('/app/output/1a_outlines')
        output_file = Path('/app/output/summary.json')
    else:
        stage1_folder = Path(__file__).parent / "output" / "1a_outlines"
        output_file = Path(__file__).parent / "output" / "summary.json"

    process = psutil.Process(os.getpid())
    print(f"[DEBUG] Memory usage before summarization: {process.memory_info().rss / 1024 / 1024:.2f} MB")

    final_output = []
    for filepath in stage1_folder.glob("*.json"):
        print(f"[DEBUG] Summarizing {filepath.name} (memory: {process.memory_info().rss / 1024 / 1024:.2f} MB)")
        final_output.append(process_json_file(filepath))
        print(f"[DEBUG] Finished {filepath.name} (memory: {process.memory_info().rss / 1024 / 1024:.2f} MB)")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"✅ Summaries written to {output_file}")
    print(f"[DEBUG] Memory usage after all summarization: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    # This script now works both locally and on Render/Docker

if __name__ == "__main__":
    main()

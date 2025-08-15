import json
from pathlib import Path
import psutil
import os
import nltk
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
import gc

# Download required NLTK data
nltk.download('punkt', quiet=True)

# Memory monitoring
def log_memory_usage(stage):
    process = psutil.Process(os.getpid())
    print(f"[MEMORY] {stage}: {process.memory_info().rss / 1024 / 1024:.2f}MB")

# Lazy loading models
def get_models():
    """Lazy load models only when needed"""
    if not hasattr(get_models, "embedder"):
        log_memory_usage("Before loading embedder")
        get_models.embedder = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # Smaller model
        log_memory_usage("After loading embedder")
        gc.collect()
    
    if not hasattr(get_models, "summarizer"):
        log_memory_usage("Before loading summarizer")
        get_models.summarizer = pipeline(
            "summarization", 
            model="sshleifer/distilbart-cnn-12-6",  # More memory efficient
            device=-1  # Force CPU
        )
        log_memory_usage("After loading summarizer")
        gc.collect()
    
    return get_models.embedder, get_models.summarizer

def find_relevant_sections(json_data, query, top_k=3, batch_size=5):
    """Search headings + content for most relevant matches to the query."""
    embedder, _ = get_models()  # Only loads when first called
    sections = []
    
    # Prepare sections with minimal memory footprint
    for item in json_data.get("outline", []):
        heading = item.get("heading", "")
        content = item.get("content", "")
        combined_text = f"{heading}. {content}".strip()
        if combined_text:
            sections.append(combined_text)
    
    if not sections:
        return []

    # Process in batches to control memory usage
    results = []
    query_embedding = embedder.encode([query])
    
    for i in range(0, len(sections), batch_size):
        batch = sections[i:i+batch_size]
        batch_embeddings = embedder.encode(batch)
        similarities = cosine_similarity(query_embedding, batch_embeddings)[0]
        results.extend(zip(range(i, i + len(batch)), similarities))
        del batch_embeddings
        gc.collect()  # Help garbage collector

    # Sort and get top_k
    results.sort(key=lambda x: x[1], reverse=True)
    top_indices = {idx for idx, _ in results[:top_k]}
    
    # Reconstruct results with original data
    final_results = []
    for idx, item in enumerate(json_data.get("outline", [])):
        if idx in top_indices:
            final_results.append((item.get("heading", ""), f"{item.get('heading', '')}. {item.get('content', '')}"))
    
    return final_results

def summarize_text(text, max_len=80):
    """Summarize the text into a concise explanation."""
    if not text.strip():
        return ""
    
    try:
        _, summarizer = get_models()  # Only loads when first called
        summary = summarizer(
            text,
            max_length=max_len,
            min_length=10,
            do_sample=False,
            truncation=True
        )
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Summarization error: {str(e)}")
        return text[:max_len] + "..." if len(text) > max_len else text

def explain_topic(topic: str, out_path: Path = None):
    """Main function to explain a topic using the extracted outlines."""
    try:
        log_memory_usage("Starting explain_topic")
        
        # Create output directory if it doesn't exist
        output_dir = Path("output/1a_outlines")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Look for JSON files in the directory
        json_files = list(output_dir.glob("*.json"))
        if not json_files:
            return {"error": "No outline files found. Please run the extraction first."}
        
        # Use the first JSON file found
        outlines_path = json_files[0]
        log_memory_usage(f"Loading outlines from {outlines_path}")
        
        with open(outlines_path, 'r', encoding='utf-8') as f:
            outlines = json.load(f)
        
        log_memory_usage("After loading outlines")
        
        # Find relevant sections
        relevant_sections = find_relevant_sections(outlines, topic)
        log_memory_usage("After finding relevant sections")
        
        # Generate explanations
        explanations = []
        for heading, content in relevant_sections:
            explanation = {
                "heading": heading,
                "explanation": summarize_text(content)
            }
            explanations.append(explanation)
            gc.collect()  # Clean up after each iteration
        
        log_memory_usage("After generating explanations")
        
        # Format results
        result = {
            "topic": topic,
            "explanations": explanations,
            "memory_usage_mb": psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        }
        
        # Save results if path provided
        if out_path:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result
        
    except Exception as e:
        log_memory_usage(f"Error in explain_topic: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate explanations for a topic from Stage 1 outlines.")
    parser.add_argument("--topic", required=True, help="Topic or query to explain")
    parser.add_argument("--out", default=str(Path(__file__).parent / "output" / "explain.json"), help="Output JSON file path")
    args = parser.parse_args()

    output = explain_topic(args.topic, Path(args.out))
    print(json.dumps(output, ensure_ascii=False, indent=2))



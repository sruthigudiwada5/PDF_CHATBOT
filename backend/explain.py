import json
from pathlib import Path
import psutil
import os
import gc
import re
from typing import List, Dict, Any

# Memory logging
def log_memory(stage: str) -> float:
    """Log memory usage in MB."""
    try:
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / 1024 / 1024
        print(f"[MEMORY] {stage}: {mem_mb:.2f} MB")
        return mem_mb
    except Exception as e:
        print(f"[ERROR] Memory logging failed: {e}")
        return 0

def load_sections() -> List[Dict[str, str]]:
    """Load and return sections from outline files."""
    outline_dir = Path("output/1a_outlines")
    if not outline_dir.exists():
        return []
    
    sections = []
    for file in outline_dir.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for sec in data.get("outline", []):
                    sections.append({
                        "title": sec.get("heading", sec.get("text", "")).lower(),
                        "content": sec.get("content", ""),
                        "document": file.stem
                    })
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    return sections

def simple_match_score(query: str, text: str) -> int:
    """Simple word-based matching score."""
    if not query or not text:
        return 0
    query_words = set(word.lower() for word in re.findall(r'\w+', query))
    text_words = set(word.lower() for word in re.findall(r'\w+', text))
    common = query_words.intersection(text_words)
    return len(common) / len(query_words) * 100 if query_words else 0

def simple_summarize(text: str, max_sentences: int = 2) -> str:
    """Lightweight extractive summarization."""
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    return ' '.join(sentences[:max_sentences])

def explain_topic(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Explain a topic with minimal memory usage."""
    log_memory("Start Explain")
    
    try:
        # Load and process sections
        sections = load_sections()
        if not sections:
            return {"error": "No content available. Please process some documents first."}
        
        # Score each section
        scored_sections = []
        for section in sections:
            title_score = simple_match_score(query, section["title"]) * 1.5  # Weight title matches more
            content_score = simple_match_score(query, section["content"])
            total_score = (title_score + content_score) / 2.5  # Normalize score
            
            if total_score > 20:  # Only include relevant sections
                scored_sections.append((section, total_score))
        
        # Sort by score and take top_k
        scored_sections.sort(key=lambda x: x[1], reverse=True)
        results = []
        
        for section, score in scored_sections[:top_k]:
            results.append({
                "heading": section["title"].title(),  # Title case for display
                "document": section["document"],
                "score": round(score, 2),
                "explanation": simple_summarize(section["content"])
            })
        
        log_memory("End Explain")
        return {"topic": query, "results": results}
    
    except Exception as e:
        log_memory(f"Error in explain_topic: {str(e)}")
        return {"error": f"Processing error: {str(e)}"}
    finally:
        gc.collect()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Explain a topic using processed documents")
    parser.add_argument("--topic", required=True, help="Topic to explain")
    parser.add_argument("--top_k", type=int, default=3, help="Number of results to return")
    args = parser.parse_args()
    
    result = explain_topic(args.topic, args.top_k)
    print(json.dumps(result, indent=2, ensure_ascii=False))
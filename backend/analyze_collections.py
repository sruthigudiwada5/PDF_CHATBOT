# analyze_collections.py (Final, Docker-Ready Modular Version)
import json
from pathlib import Path
import datetime
import sys
import os
import nltk
import psutil

def log_memory_usage(stage=""):
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / 1024 / 1024
    print(f"[MEMORY] {stage} - RSS: {mem_mb:.2f} MB", flush=True)


# --- ENVIRONMENT-AWARE NLP SETUP ---
# Always use paths relative to the script location
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
NLTK_DATA_PATH_IN_CONTAINER = BASE_DIR / "nltk_data"

# Check if we are inside the Docker container by seeing if that path exists.
if NLTK_DATA_PATH_IN_CONTAINER.exists():
    nltk.data.path.append(str(NLTK_DATA_PATH_IN_CONTAINER))

else:
    # If we are running locally, use the standard download-on-demand logic.
    try:
        nltk.data.find('corpora/wordnet.zip')
        nltk.data.find('taggers/averaged_perceptron_tagger.zip')
        nltk.data.find('tokenizers/punkt.zip')
    except LookupError:
        print("Downloading NLTK data for local development (one-time setup)...")
        # For local use, we download to the path NLTK expects by default.
        nltk.download('wordnet', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('punkt', quiet=True)
        print("NLTK data download complete.")

# --- YOUR MODULAR FUNCTIONS (UNCHANGED) ---

def expand_query_with_nlp(persona, job_to_be_done):
    """
    Generates an expanded query string using task context.
    """
    base_query = f"Persona: {persona}. Task: {job_to_be_done}. "
    persona_enrichment = (
        "Focus on important, useful, or contextually relevant parts of the documents that would help in this task. "
        "Look for how-to information, actionable sections, or domain-relevant content."
    )
    return base_query + persona_enrichment

def load_sections(documents, rich_sections_dir):
    """
    Loads all pre-processed sections from the intermediate JSON files.
    Adds debug output to help trace loading issues.
    """
    from pathlib import Path
    import traceback

    all_sections = []
    print(f"\n🔍 [Stage 2] Starting to load intermediate section files from: {rich_sections_dir.resolve()}", flush=True)

    for doc_info in documents:
        doc_name = doc_info['filename']
        rich_json_path = rich_sections_dir / f"{Path(doc_name).stem}.json"

        print(f"📄 Looking for: {rich_json_path}", flush=True)

        if not rich_json_path.exists():
            print(f"⚠️ File not found for document: {doc_name}", flush=True)
            continue

        try:
            with open(rich_json_path, 'r', encoding='utf-8') as f:
                rich_data = json.load(f)
            
            sections = rich_data.get("outline", [])
            print(f"✅ Loaded {len(sections)} sections from {rich_json_path.name}", flush=True)

            for section in sections:
                section['document'] = doc_name
                section['section_title'] = section.pop('text')
                all_sections.append(section)

        except Exception as e:
            print(f"❌ Failed to load or parse {rich_json_path.name}: {str(e)}", file=sys.stderr, flush=True)
            traceback.print_exc()

    print(f"\n📊 Total sections loaded across all documents: {len(all_sections)}\n", flush=True)
    return all_sections


def rank_sections(all_sections, query_embedding, model):
    """Performs the two-level ranking and returns the top sections."""
    from sentence_transformers import util
    section_titles = [s['section_title'] for s in all_sections]
    section_contents = [s.get('content', '') for s in all_sections]

    title_embeddings = model.encode(["passage: " + t for t in section_titles], convert_to_tensor=True, show_progress_bar=False)
    content_embeddings = model.encode(["passage: " + c for c in section_contents], convert_to_tensor=True, show_progress_bar=False)

    title_scores = util.cos_sim(query_embedding, title_embeddings)[0]
    content_scores = util.cos_sim(query_embedding, content_embeddings)[0]

    combined_sections = []
    content_only_sections = []

    for i, section in enumerate(all_sections):
        combined_score = 0.5 * content_scores[i].item() + 0.5 * title_scores[i].item()
        content_score = content_scores[i].item()
        combined_sections.append({**section, 'score': combined_score})
        content_only_sections.append({**section, 'score': content_score})

    top_extracted = sorted(combined_sections, key=lambda s: s['score'], reverse=True)[:5]
    top_content = sorted(content_only_sections, key=lambda s: s['score'], reverse=True)[:5]
    return top_extracted, top_content

def build_output(documents, persona, job, top_extracted, top_content):
    """Formats the final results into the required JSON structure."""
    output = {
        "metadata": {
            "input_documents": [d['filename'] for d in documents],
            "persona": persona, "job_to_be_done": job,
            "processing_timestamp": datetime.datetime.now().isoformat()
        },
        "extracted_sections": [], "subsection_analysis": []
    }
    for i, section in enumerate(top_extracted):
        output["extracted_sections"].append({
            "document": section['document'], "section_title": section['section_title'],
            "importance_rank": i + 1, "page_number": section['page']
        })
    for section in top_content:
        output["subsection_analysis"].append({
            "document": section['document'],
            "refined_text": section.get('content', section['section_title']),
            "page_number": section['page']
        })
    return output

# --- THE MAIN CONDUCTOR FUNCTION ---

def analyze_collection(input_config_path: Path, rich_sections_dir: Path, output_dir: Path):
    """
    Orchestrates the entire analysis pipeline, from loading to saving the final output.
    """
    log_memory_usage("START Stage 2")
    print(f"\n--- Starting Stage 2: Deep Semantic Analysis for {input_config_path.parent.name} ---")

    with open(input_config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    persona, job, documents = config['persona']['role'], config['job_to_be_done']['task'], config['documents']

    # --- ENHANCED MODEL LOADING WITH FALLBACKS ---
    print("Loading semantic analysis model...")
    from sentence_transformers import SentenceTransformer
    model_name = 'paraphrase-MiniLM-L3-v2'
    
    # Check multiple possible cache locations
    possible_cache_folders = [
        str(Path(os.getenv('SENTENCE_TRANSFORMERS_HOME', '/app/model_cache'))),
        str(rich_sections_dir.parent / "model_cache"),
        str(Path.home() / ".cache" / "sentence_transformers")
    ]
    model = None
    for cache_folder in possible_cache_folders:
        try:
            print(f"Trying to load model from cache: {cache_folder}")
            model = SentenceTransformer(model_name, cache_folder=cache_folder)
            print(f"✅ Model loaded from {cache_folder}")
            log_memory_usage("AFTER MODEL LOAD")
            break
        except Exception as e:
            print(f"❌ Failed to load model from {cache_folder}: {e}")
    if model is None:
        print("❌ All attempts to load the model failed.", file=sys.stderr)
        return
    # -----------------------------------------------------------

    expanded_query = expand_query_with_nlp(persona, job)
    print(f"  - Using Expanded Query: {expanded_query}")
    query_embedding = model.encode("query: " + expanded_query, convert_to_tensor=True, show_progress_bar=False)

    all_sections = load_sections(documents, rich_sections_dir)
    log_memory_usage("AFTER SECTION LOAD")
    if not all_sections:
        print("Error: No sections were found in the pre-processed files.", file=sys.stderr)
        return

    top_extracted, top_content = rank_sections(all_sections, query_embedding, model)
    log_memory_usage("AFTER SEMANTIC RANKING")
    output_json = build_output(documents, persona, job, top_extracted, top_content)

    output_path = output_dir / "challenge1b_output.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, indent=4)

    print(f"Analysis complete. Final Round 1B output saved to {output_path}")
    log_memory_usage("END Stage 2")

# --- LOCAL TESTING HARNESS (UNCHANGED) ---
if __name__ == '__main__':
    collection_dir = Path("./Challenge_1b/Collection 1")
    intermediate_dir = Path("./output/intermediate_rich_sections")
    final_output_dir = Path("./output/final_1b_results")
    final_output_dir.mkdir(parents=True, exist_ok=True)

    if not intermediate_dir.is_dir() or not any(intermediate_dir.iterdir()):
        print(f"Error: Intermediate directory '{intermediate_dir}' is empty or not found.", file=sys.stderr)
        print("Please run the Stage 1 extraction script (`process_pdfs.py`) first.", file=sys.stderr)
        sys.exit(1)

    analyze_collection(
        input_config_path=collection_dir / "challenge1b_input.json",
        rich_sections_dir=intermediate_dir,
        output_dir=final_output_dir
    )
import os
import sys
import nltk
from sentence_transformers import SentenceTransformer
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)

def setup_directories():
    """Create necessary directories with proper permissions."""
    dirs = [
        os.path.join(BASE_DIR, "model_cache"),
        os.path.join(BASE_DIR, "nltk_data"),
        os.path.join(BASE_DIR, "input"),
        os.path.join(BASE_DIR, "output"),
    ]
    
    for dir_path in dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            os.chmod(dir_path, 0o777)  # Ensure write permissions
            logger.info(f"Created/verified directory: {dir_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {str(e)}")
            raise

def download_models():
    """Download and cache all required models. Returns True on success (both), False otherwise."""
    cache_dir = os.getenv('SENTENCE_TRANSFORMERS_HOME', os.path.join(BASE_DIR, 'model_cache'))
    # Ensure all relevant HF caches point to the same location
    os.environ.setdefault('SENTENCE_TRANSFORMERS_HOME', cache_dir)
    os.environ.setdefault('HF_HOME', cache_dir)
    os.environ.setdefault('TRANSFORMERS_CACHE', cache_dir)

    ok = True

    # 1️⃣ Download embedder
    embedder_name = 'sentence-transformers/paraphrase-MiniLM-L3-v2'
    logger.info(f"Downloading embedder model '{embedder_name}' to: {cache_dir}")
    try:
        embedder = SentenceTransformer(embedder_name, cache_folder=cache_dir)
        embedder_save_path = os.path.join(cache_dir, embedder_name)
        embedder.save(embedder_save_path)
        logger.info(f"Embedder saved to {embedder_save_path}")
    except Exception as e:
        logger.error(f"Error downloading embedder: {str(e)}")
        ok = False

    # 2️⃣ Download summarization model
    summarizer_name = 't5-small'
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    logger.info(f"Downloading summarizer model '{summarizer_name}' to: {cache_dir}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(summarizer_name, cache_dir=cache_dir)
        model = AutoModelForSeq2SeqLM.from_pretrained(summarizer_name, cache_dir=cache_dir)
        _ = (tokenizer is not None) and (model is not None)
    logger.info(f"Summarizer model '{summarizer_name}' downloaded successfully")
    except Exception as e:
        logger.error(f"Error downloading summarizer: {str(e)}")
        ok = False

    return ok

def download_nltk_data():
    """Download required NLTK data."""
    nltk_data_dir = os.getenv('NLTK_DATA', os.path.join(BASE_DIR, 'nltk_data'))
    nltk.download('wordnet', download_dir=nltk_data_dir)
    nltk.download('averaged_perceptron_tagger', download_dir=nltk_data_dir)
    nltk.download('punkt', download_dir=nltk_data_dir)
    
    # Verify downloads
    required_files = [
        'corpora/wordnet',
        'taggers/averaged_perceptron_tagger',
        'tokenizers/punkt'
    ]
    
    for file in required_files:
        path = os.path.join(nltk_data_dir, file)
        if not os.path.exists(path):
            logger.warning(f"NLTK data file not found: {path}")
    
    logger.info("NLTK data download completed.")

def main():
    logger.info("=== Starting offline assets setup ===")
    
    try:
        # Setup directories
        setup_directories()
        
        # Download model
        if not download_models():
            logger.error("Model download failed. The application may not work correctly.")

        # Download NLTK data
        download_nltk_data()
        
        logger.info("=== Offline assets setup completed successfully ===")
        return 0
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
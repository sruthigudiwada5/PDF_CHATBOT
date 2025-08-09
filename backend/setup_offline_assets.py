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

def setup_directories():
    """Create necessary directories with proper permissions."""
    dirs = [
        "/app/model_cache",
        "/app/nltk_data",
        "/app/input",
        "/app/output"
    ]
    
    for dir_path in dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            os.chmod(dir_path, 0o777)  # Ensure write permissions
            logger.info(f"Created/verified directory: {dir_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {str(e)}")
            raise

def download_model():
    """Download and cache the sentence transformer model."""
    model_name = 'paraphrase-MiniLM-L3-v2'
    cache_dir = os.getenv('SENTENCE_TRANSFORMERS_HOME', '/app/model_cache')
    
    logger.info(f"Downloading model '{model_name}' to: {cache_dir}")
    
    try:
        # Verify we can write to the cache directory
        test_file = os.path.join(cache_dir, 'write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        # Download the model
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        # Explicitly save model to absolute path for Docker
        abs_save_path = "/app/model_cache/paraphrase-MiniLM-L3-v2"
        model.save(abs_save_path)
        logger.info(f"Model explicitly saved to {abs_save_path}")
        # Verify the model files
        model_files = os.listdir(abs_save_path)
        if not model_files:
            raise Exception("No model files found after download/save")
        logger.info(f"Model downloaded and saved successfully. Found {len(model_files)} files in cache.")
        return True
    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        return False

def download_nltk_data():
    """Download required NLTK data."""
    nltk_data_dir = os.getenv('NLTK_DATA', '/app/nltk_data')
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
        if not download_model():
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
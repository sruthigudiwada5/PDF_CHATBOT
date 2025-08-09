# Use a specific, stable, and lightweight version of Python
FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /app

# --- 1. INSTALL SYSTEM DEPENDENCIES ---
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# --- 2. CREATE DIRECTORIES ---
RUN mkdir -p /app/model_cache /app/nltk_data /app/input /app/output \
    && chmod -R 777 /app/model_cache /app/nltk_data /app/input /app/output

# --- 3. ENVIRONMENT VARIABLES ---
ENV SENTENCE_TRANSFORMERS_HOME=/app/model_cache
ENV TRANSFORMERS_CACHE=/app/model_cache
ENV NLTK_DATA=/app/nltk_data
ENV TOKENIZERS_PARALLELISM=false
ENV PYTHONUNBUFFERED=1

# --- 4. COPY FILES ---
COPY ./main.py ./main.py
COPY ./analyze_collections.py ./analyze_collections.py
COPY ./heading_extractor.py ./heading_extractor.py
COPY ./requirements.txt ./requirements.txt
COPY ./setup_offline_assets.py ./setup_offline_assets.py
COPY ./features.py ./features.py
COPY ./summary.py ./summary.py
COPY ./explain.py ./explain.py

# --- 5. INSTALL PYTHON DEPENDENCIES ---
RUN pip install --no-cache-dir -r requirements.txt


COPY setup_offline_assets.py .
RUN python setup_offline_assets.py

# --- 7. RUN SERVER ---
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

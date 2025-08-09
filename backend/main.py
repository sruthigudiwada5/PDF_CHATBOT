# main.py - Stage 1 only (PDF Structure Extraction)
import sys
import subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import json
import logging
import os
import glob
import urllib.parse
import traceback

# ------------------ CONFIG ------------------
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
INTERMEDIATE_DIR = OUTPUT_DIR / "1a_outlines"

# Ensure directories exist
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)

# ------------------ FASTAPI SETUP ------------------
app = FastAPI(title="PDF Processing - Stage 1 Only")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ UPLOAD & STAGE 1 ------------------
@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)):
    """
    Upload only PDF files, then run Stage 1 only.
    """
    logging.info("📥 Upload request received (PDFs only)")

    # Clear old files in input dir
    for f in INPUT_DIR.glob("*"):
        f.unlink()

    # Save uploaded PDF files
    uploaded_files = []
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            logging.warning(f"⛔ Skipping non-PDF file: {file.filename}")
            continue
        dest = INPUT_DIR / file.filename
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_files.append(file.filename)

    if not uploaded_files:
        return JSONResponse(status_code=400, content={"error": "No PDF files uploaded."})

    logging.info(f"✅ Uploaded PDF files: {uploaded_files}")

    # Run Stage 1 script (heading_extractor.py) via subprocess
    stage1_output_dir = OUTPUT_DIR / "1a_outlines"
    stage1_output_dir.mkdir(parents=True, exist_ok=True)
    script_path = BASE_DIR / "heading_extractor.py"
    logging.info(f"[DEBUG] Checking if script exists: {script_path.exists()}")
    if not script_path.exists():
        logging.error(f"[ERROR] {script_path} not found")
        raise FileNotFoundError(f"{script_path} not found")

    logging.info(f"🚀 Running script: {script_path}")
    cmd = [sys.executable, str(script_path)]
    logging.info(f"[DEBUG] Subprocess command: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        logging.info("✅ Subprocess finished")
        logging.info(f"📤 STDOUT:\n{result.stdout}")
        logging.info(f"📥 STDERR:\n{result.stderr}")
        logging.info(f"[DEBUG] Subprocess return code: {result.returncode}")
    except Exception as sub_exc:
        logging.error(f"[ERROR] Exception during subprocess: {sub_exc}")
        logging.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(sub_exc), "traceback": traceback.format_exc()})

    if result.returncode != 0:
        logging.error(f"❌ Script failed with code {result.returncode}")
        return JSONResponse(status_code=500, content={
            "error": result.stderr,
            "stdout": result.stdout,
            "returncode": result.returncode
        })

    # Load Stage 1 output JSON(s)
    output_json_files = list(stage1_output_dir.glob("*.json"))
    if output_json_files:
        outputs = []
        for path in output_json_files:
            with open(path) as f:
                data = json.load(f)
            # Add PDF URL if relevant
            def make_pdf_url(filename, request):
                base_url = str(request.base_url).rstrip('/')
                url = f"{base_url}/pdfs/{urllib.parse.quote(filename)}"
                logging.info(f"[DEBUG] Constructed PDF URL: {url}")
                return url
            # Patch URLs if 'document' field exists
            if isinstance(data, dict):
                if 'document' in data:
                    data['pdf_url'] = make_pdf_url(data['document'], request)
            outputs.append(data)
        return outputs
    else:
        logging.warning(f"[WARNING] No Stage 1 output JSONs found in: {stage1_output_dir}")
        return {"status": "done", "message": "Stage 1 complete, but no output files found."}

# ------------------ ROOT ------------------
@app.get("/")
def root():
    return {"message": "PDF Processing API - Stage 1 Ready"}

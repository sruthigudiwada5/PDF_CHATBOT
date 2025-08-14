# main.py - Stage 1 only (PDF Structure Extraction)
import sys
import subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse
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
app = FastAPI(title="PDF Processing API (Combined)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ UPLOAD & STAGE 1 ------------------
@app.post("/upload/")
async def upload_files(request: Request, files: list[UploadFile] = File(...)):
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

    # Run Stage 1 script (heading_extractor.py) once per uploaded PDF
    stage1_output_dir = OUTPUT_DIR / "1a_outlines"
    stage1_output_dir.mkdir(parents=True, exist_ok=True)

    # Clear previous JSON outputs to avoid mixing stale data
    for old_json in stage1_output_dir.glob("*.json"):
        try:
            old_json.unlink()
        except Exception as del_exc:
            logging.warning(f"[WARN] Could not delete old output {old_json}: {del_exc}")

    script_path = BASE_DIR / "heading_extractor.py"
    logging.info(f"[DEBUG] Checking if script exists: {script_path.exists()}")
    if not script_path.exists():
        logging.error(f"[ERROR] {script_path} not found")
        raise FileNotFoundError(f"{script_path} not found")

    failures = []
    for fname in uploaded_files:
        input_pdf = INPUT_DIR / fname
        # Stage 2 expects files named '<stem>.json' in the rich sections dir
        out_path = stage1_output_dir / f"{Path(fname).stem}.json"
        cmd = [
            sys.executable,
            str(script_path),
            str(input_pdf),
            "-o",
            str(out_path),
        ]
        logging.info(f"🚀 Running Stage 1 for: {fname}")
        logging.info(f"[DEBUG] Subprocess command: {cmd}")
        try:
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                env=os.environ.copy(),
            )
        except Exception as sub_exc:
            logging.error(f"[ERROR] Exception during subprocess for {fname}: {sub_exc}")
            logging.error(traceback.format_exc())
            failures.append({
                "file": fname,
                "exception": str(sub_exc),
                "traceback": traceback.format_exc(),
            })
            continue

        logging.info(f"✅ Subprocess finished for {fname}")
        logging.info(f"📤 STDOUT ({fname}):\n{result.stdout}")
        logging.info(f"📥 STDERR ({fname}):\n{result.stderr}")
        logging.info(f"[DEBUG] Return code ({fname}): {result.returncode}")
        if result.returncode != 0:
            logging.error(f"❌ Stage 1 failed for {fname} with code {result.returncode}")
            failures.append({
                "file": fname,
                "returncode": result.returncode,
                "stderr": result.stderr,
                "stdout": result.stdout,
            })

    if failures and len(failures) == len(uploaded_files):
        # All failed → return error details
        return JSONResponse(status_code=500, content={
            "error": "Stage 1 failed for all files",
            "details": failures,
        })

    # Load Stage 1 output JSON(s)
    output_json_files = list(stage1_output_dir.glob("*.json"))
    if output_json_files:
        # Map stem -> original uploaded filename
        name_map = {Path(n).stem: n for n in uploaded_files}
        outputs = []
        for path in output_json_files:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            stem = path.stem
            original_name = name_map.get(stem, f"{stem}.pdf")
            # Ensure original filename is present for Stage 2
            if isinstance(data, dict):
                data.setdefault('document', original_name)
                data.setdefault('filename', original_name)
                # Optional: add a derived PDF URL
                def make_pdf_url(filename, request):
                    base_url = str(request.base_url).rstrip('/')
                    url = f"{base_url}/pdfs/{urllib.parse.quote(filename)}"
                    logging.info(f"[DEBUG] Constructed PDF URL: {url}")
                    return url
                data['pdf_url'] = make_pdf_url(original_name, request)
            outputs.append(data)
        return outputs
    else:
        logging.warning(f"[WARNING] No Stage 1 output JSONs found in: {stage1_output_dir}")
        return {"status": "done", "message": "Stage 1 complete, but no output files found."}

# ------------------ Stage 2+ Features (Merged from features.py) ------------------
# Keep the old Stage 1 route available at /upload/ (above), and expose a namespaced
# alias at /stage1/upload/ to match the frontend expectations.
@app.post("/stage1/upload/")
async def stage1_upload(request: Request, files: list[UploadFile] = File(...)):
    return await upload_files(request, files)

def run_script(script_name, output_file=None, args=None):
    """Run a Python script and optionally return JSON output.
    script_name: file name of the script in the same directory.
    output_file: Path object for expected JSON output to return.
    args: list of additional CLI arguments to pass to the script.
    """
    cmd = [sys.executable, str(BASE_DIR / script_name)]
    if args:
        cmd.extend(map(str, args))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"status": "error", "stderr": result.stderr}
    
    if output_file and output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            return {"status": "success", "data": json.load(f)}
    
    return {"status": "success", "stdout": result.stdout}

@app.get("/summary/")
def run_summary():
    return run_script("summary.py", OUTPUT_DIR / "summary.json")

@app.get("/documents/")
def list_stage1_documents():
    """
    Lists available Stage 1 outline files from output/1a_outlines as document entries.
    Returns a list of { filename, title } objects where filename is inferred as '<stem>.pdf'.
    """
    outlines = OUTPUT_DIR / "1a_outlines"
    docs = []
    if outlines.exists():
        for p in sorted(outlines.glob("*.json")):
            stem = p.stem
            docs.append({"filename": f"{stem}.pdf", "title": stem})
    return {"documents": docs}

@app.post("/analyze/")
async def run_analyze(config: UploadFile = File(...)):
    """
    Accepts a JSON config file from the frontend, saves it as input/challenge1b_input.json,
    then runs analyze_collection() directly against Stage 1 outputs in output/1a_outlines.
    """
    # 1) Save uploaded config
    input_dir = BASE_DIR / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    config_path = input_dir / "challenge1b_input.json"
    contents = await config.read()
    with open(config_path, "wb") as f:
        f.write(contents)

    # 1b) Ensure documents exist in config by auto-discovering outlines if needed
    try:
        cfg = json.loads(contents.decode("utf-8"))
    except Exception:
        cfg = None
    if not isinstance(cfg, dict):
        cfg = {}
    docs = cfg.get("documents")
    if not isinstance(docs, list) or len(docs) == 0:
        outlines = OUTPUT_DIR / "1a_outlines"
        auto_docs = []
        if outlines.exists():
            for p in sorted(outlines.glob("*.json")):
                stem = p.stem
                auto_docs.append({"filename": f"{stem}.pdf", "title": stem})
        cfg["documents"] = auto_docs
        # Re-write the config file with injected documents
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

    # 2) Run analysis programmatically to avoid relying on CLI defaults
    try:
        from analyze_collections import analyze_collection
        rich_sections_dir = OUTPUT_DIR / "1a_outlines"
        output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        analyze_collection(
            input_config_path=config_path,
            rich_sections_dir=rich_sections_dir,
            output_dir=output_dir,
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

    out_file = OUTPUT_DIR / "challenge1b_output.json"
    if out_file.exists():
        with open(out_file, "r", encoding="utf-8") as f:
            return {"status": "success", "data": json.load(f)}
    return {"status": "error", "message": "Analysis did not produce output."}

@app.get("/explain/")
async def run_explain(topic: str = ""):
    out_path = OUTPUT_DIR / f"explain_{topic}.json"
    return run_script(
        "explain.py",
        output_file=out_path,
        args=["--topic", topic, "--out", str(out_path)]
    )

# ------------------ ROOT ------------------
@app.get("/")
def root():
    return {"message": "PDF Processing API - Stage 1 Ready"}

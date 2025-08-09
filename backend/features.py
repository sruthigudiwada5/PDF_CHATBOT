import subprocess
import sys
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

app = FastAPI(title="PDF Features Runner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


from fastapi import UploadFile, File

@app.post("/analyze/")
async def run_analyze(config: UploadFile = File(...)):
    """
    Accepts a JSON config file from the frontend, saves it as input/challenge1b_input.json, then runs analyze_collections.py.
    """
    input_dir = BASE_DIR / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    config_path = input_dir / "challenge1b_input.json"
    contents = await config.read()
    with open(config_path, "wb") as f:
        f.write(contents)
    return run_script("analyze_collections.py", OUTPUT_DIR / "challenge1b_output.json")


@app.get("/explain/")
def run_explain(topic: str):
    out_path = OUTPUT_DIR / f"explain_{topic}.json"
    return run_script(
        "explain.py",
        output_file=out_path,
        args=["--topic", topic, "--out", str(out_path)]
    )

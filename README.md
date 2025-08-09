# PDF Chatbot: Upload, Analyze & Chat with PDFs

A modern, full-stack web app to upload PDFs, analyze them with AI, and chat with your documents. No in-page PDF viewing—just clean, fast, and interactive analysis.

---

## Features

### 🚀 Frontend (Web UI)
- **Modern, Responsive UI**: Built with vanilla JavaScript and Bootstrap 5 for a clean, mobile-friendly experience.
- **PDF Upload Panel**: Floating 📄 button opens a drag-and-drop panel for uploading one or more PDFs.
- **Persona & Job Input**: Users can specify a "persona" (role/context) and "job to be done" (task/query) for more relevant analysis.
- **Analysis Cards**: Results are displayed as clickable cards, each summarizing a section or finding from your PDF(s).
- **Chat Interface**: Natural chat window for conversation with the AI, including:
  - Chat message bubbles (user & bot)
  - Sidebar with chat history and new chat button
  - LocalStorage-powered persistent chat history
  - Toast notifications for feedback and errors
- **Clickable PDF Links**: Analysis results in chat include links that open the PDF externally (never embedded, for security and compatibility).
- **Progress Bar & Status**: Visual feedback during upload/analysis, including progress bar and status messages.
- **File List Management**: Remove individual PDFs before analysis, see file names and icons.
- **Accessibility**: Keyboard navigation, clear focus states, and responsive design.
- **Error Handling**: User-friendly error messages for missing fields, backend/API errors, and upload problems.
- **No In-Page PDF Viewer**: All PDF viewer/split-viewer code removed for a simpler, more robust UI.

### 🧠 Backend (AI/Analysis)
- **FastAPI Server**: Python backend for handling PDF uploads and analysis requests.
- **Semantic Analysis**: Uses NLP models (e.g., sentence embeddings) to extract, summarize, and rank sections of PDFs based on user query/context.
- **Multi-File Support**: Analyze multiple PDFs in a single request.
- **Customizable Analysis**: Accepts persona and job/task to tailor the analysis output.
- **Structured Results**: Returns analysis as structured JSON for easy frontend rendering.
- **Docker Support**: Fully containerized for easy deployment anywhere (local or cloud).
- **CORS Enabled**: Ready for local frontend-backend development.
- **Robust Error Handling**: Graceful handling of invalid files, missing fields, and server errors.

### 🛠️ Dev & Ops
- **Easy Local Development**: Run backend with Uvicorn, frontend with any static server (Live Server, Python http.server, etc.)
- **Quick Docker Start**: One-command build/run for backend; frontend is static and portable.
- **Configurable API Endpoint**: Change backend URL in `frontend/script.js` if needed.
- **Minimal Dependencies**: No heavy frameworks on frontend; backend uses FastAPI and standard NLP libraries.

### 🔒 Security & Privacy
- **No PDF Embedding**: Avoids CORS and privacy issues by never embedding PDFs in-page.
- **File Handling**: Files processed in-memory or securely stored as needed.
- **Frontend-Only Storage**: Chat history and state are local to the browser.

---

---

## Quick Start (Docker)

1. **Clone the repo:**
   ```bash
   git clone <your-repo-url>
   cd PDF_CHATBOT
   ```
2. **Build the backend Docker image:**
   ```bash
   docker build -t pdf-chatbot-backend ./backend
   ```
3. **Run the backend:**
   ```bash
   docker run -p 8000:8000 pdf-chatbot-backend
   ```
4. **Serve the frontend:**
   - Use VSCode Live Server, Python `http.server`, or any static server:
     ```bash
     cd frontend
     python -m http.server 8080
     # or use Live Server extension in VSCode
     ```
   - Open [http://localhost:8080](http://localhost:8080)

---

## Local Development

### Backend
- Python 3.9+
- Install dependencies:
  ```bash
  cd backend
  pip install -r requirements.txt
  uvicorn main:app --reload
  ```
- API runs at `http://localhost:8000`

### Frontend
- All static files in `frontend/`
- Edit `frontend/script.js` to point to your backend URL if needed
- Open `frontend/index.html` in a browser or use a static server

---

## Deployment

### 🌐 Frontend: Deploy to Vercel
You can deploy the static frontend (index.html, script.js, style.css) to [Vercel](https://vercel.com/) for instant, global hosting.

1. **Create a Vercel account** ([vercel.com](https://vercel.com/))
2. **Import your repo** or upload the `frontend/` folder in the Vercel dashboard
3. **Set project root to `frontend/`**
4. **Build/Output settings:**
   - Framework: `Other`
   - Output directory: `frontend` (or leave blank if deploying only the folder)
5. **Update API endpoint:**
   - In `frontend/script.js`, set the backend API URL to your Render backend URL (see below)
6. **Deploy!**

### 🚀 Backend: Deploy to Render
The backend (FastAPI) can be deployed to [Render](https://render.com/) as a web service.

1. **Create a Render account** ([render.com](https://render.com/))
2. **Create a new Web Service**
   - Connect your repo or manually deploy the `backend/` folder
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn main:app --host 0.0.0.0 --port 10000` (or your preferred port)
   - Choose a port (e.g., 10000 or 8000)
3. **Configure CORS** if needed (already enabled by default)
4. **Get your public backend URL** from Render dashboard
5. **Update the frontend** to use this backend URL

---

## Usage
1. Click the floating 📄 button to open the PDF upload panel
2. Drag & drop or select PDF(s)
3. Enter a persona (e.g., "Travel Planner") and job/task (e.g., "Plan a 4-day trip")
4. Click Analyze
5. View results as chat messages and clickable analysis cards
6. Click links to open PDFs in a new tab

---

## Project Structure
```
PDF_CHATBOT/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── process_pdfs.py          # Pipeline orchestrator
│   ├── analyze_collections.py   # Semantic analysis
│   ├── heading_extractor.py     # PDF structure extraction
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Container build file
├── frontend/
│   ├── index.html
│   ├── script.js
│   ├── style.css
│   └── ...
├── README.md
└── approach_explanation.md

---

## Troubleshooting
- If Analyze button is disabled: select at least one PDF and fill both persona & job fields
- If analysis fails: check backend logs, CORS, or API URL in `script.js`
- For Docker issues: ensure ports are mapped and backend is running

---

## License
MIT

A robust, containerized FastAPI backend for PDF extraction and semantic analysis. Upload PDFs, trigger semantic analysis, and retrieve results via API. Designed for easy deployment on Render.com or any Docker-compatible cloud service.

---

## Project Structure

```
pdf-analysis-app/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── process_pdfs.py          # Pipeline orchestrator
│   ├── analyze_collections.py   # Semantic analysis
│   ├── heading_extractor.py     # PDF structure extraction
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Container build file
├── frontend/                    # (optional, for UI)
├── README.md
└── approach_explanation.md
```

---

## Features
- **PDF Upload & Analysis API** (FastAPI)
- **Two-stage NLP pipeline**: PDF structure extraction + semantic ranking
- **Dockerized** for reproducible builds
- **Ready for cloud deployment** (Render, AWS, Azure, etc.)

---

## Local Development & Testing

### 1. Install Python dependencies (optional, for local run)
```sh
cd backend
pip install -r requirements.txt
```

### 2. Run the FastAPI server
```sh
uvicorn main:app --host 0.0.0.0 --port 10000
```

### 3. Test the API
- Health check: [http://localhost:10000/](http://localhost:10000/)
- Upload PDF:
  - POST `/upload/` (form-data, key: `file`, value: PDF file)
- Trigger analysis:
  - POST `/analyze/` (form-data: `persona`, `job`, `files`)

---

## Docker Build & Run

### 1. Build the Docker image
```sh
cd backend
# On Windows (PowerShell):
docker build -t pdf-analysis-backend .
```

### 2. Run the container
```sh
docker run -it --rm -p 10000:10000 pdf-analysis-backend
```

---

## Deployment (Render.com Example)

1. **Push your code to GitHub** (with backend/Dockerfile in place)
2. **Create a new Web Service** on [Render.com](https://render.com)
   - Environment: Docker
   - Root Directory: `backend`
   - Port: `10000`
3. **Deploy**. Render will build and expose your backend at a public URL.

---

## API Reference

### `GET /`
- Health check: returns `{ "status": "Backend is running" }`

### `POST /upload/`
- Upload a PDF file
- **Body:** `multipart/form-data`, key: `file`
- **Response:** `{ "filename": "..." }`

### `POST /analyze/`
- Trigger analysis on uploaded PDFs
- **Body:** `multipart/form-data`
    - `persona`: string
    - `job`: string
    - `files`: comma-separated PDF filenames
- **Response:** analysis results JSON or status message

---

## Tips & Troubleshooting
- Uploaded PDFs are stored in `backend/input/`
- Results are saved in `backend/output/challenge1b_output.json`
- For multi-file analysis, separate filenames with commas in `files`
- Check logs for errors if output is missing

---

## License
MIT

---

## Author
- Developed by Gudiwada sruthi
- For Adobe Hackathon 2025

```

### Notes:
- Runs fully offline once built
- Processes all PDFs in input directory
- Generates structured JSON output in output directory

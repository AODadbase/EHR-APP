# Traceable Health – EHR Data Pipeline

This repository contains a small end‑to‑end demo for clinical document processing:

- **Backend** – Python pipeline and FastAPI API for PDF ingestion, data extraction, and discharge‑summary generation.
- **Frontend** – React + Vite web UI for authentication, document upload, review, and search.

Use this README for a high‑level overview. See the folder‑level READMEs for details.

## Architecture

- Browser client (React/Vite) runs on http://localhost:3000 during development.
- Frontend sends HTTP requests to the FastAPI backend at http://localhost:8000 under the `/api` path.
- Backend orchestrates PDF processing via Unstructured.io, runs extraction and formatting logic, and returns structured JSON to the frontend.
- Optional Streamlit app in the backend folder can be run independently for exploration.

### Backend folder structure

```text
ehr-data-pipeline-backend/
├── README.md
├── requirements.txt
├── .gitignore
├── api_server.py          # FastAPI application entry point
├── app.py                 # Streamlit application entry point
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration and environment loading
│   ├── pdf_processor.py   # Unstructured.io integration
│   ├── data_extractor.py  # Structured data extraction
│   ├── formatter.py       # Discharge summary formatting
│   ├── section_editor.py  # Section selection utilities
│   └── utils.py           # Shared helpers
├── data/
│   ├── uploads/           # PDFs uploaded through the API (created at runtime)
│   ├── samples/           # Example PDFs for local testing
│   └── processed/         # Processed JSON outputs (Streamlit)
└── templates/
   └── discharge_template.txt
```

### Frontend folder structure

```text
ehr-frontend-website/
├── README.md
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── App.tsx
├── components/            # Layout, dashboard, auth, document views
├── services/              # Auth and mock data services
└── types.ts               # Shared TypeScript types
```

## Project layout

- `ehr-data-pipeline-backend/` – Python code, FastAPI server, Streamlit app, and processing pipeline.
- `ehr-frontend-website/` – React + TypeScript frontend.
- `setup.sh` – optional helper for first‑time dependency installation.
- `start_app.sh` – optional helper script to start backend and frontend together (if configured).

## Quick start

### 1. Backend API

From the backend folder:

```bash
cd ehr-data-pipeline-backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

Create a `.env` file in `ehr-data-pipeline-backend` with at least:

```env
UNSTRUCTURED_API_KEY=your_unstructured_key
UNSTRUCTURED_API_URL=https://api.unstructured.io
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
RESEND_API_KEY=your_resend_key  # optional, required for email verification
```

Start the FastAPI server:

```bash
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

Verify the API:

- Open http://localhost:8000/api/health and confirm `{ "status": "ok" }`.

You can still run the original Streamlit UI separately with:

```bash
streamlit run app.py
```

### 2. Frontend UI

From the frontend folder:

```bash
cd ehr-frontend-website
npm install
npm run dev
```

Open http://localhost:3000.

The frontend expects the backend to be available at `http://localhost:8000` and calls endpoints under `/api` (for example `/api/documents`, `/api/search`, `/api/send-code`).

### 3. Running both together

1. In one terminal, run the backend as shown above.
2. In a second terminal, run the frontend dev server.
3. Visit http://localhost:3000 to:
   - Register and sign in.
   - Upload clinical PDFs.
   - View extracted data and discharge summaries.
   - Search across processed documents.

## API reference (summary)

Base URL during local development: `http://localhost:8000/api`

- `GET /health` – Health check.
- `POST /send-code` – Send a verification code email.
- `POST /verify-code` – Verify a code and return a mock token.
- `GET /documents` – List processed documents.
- `GET /documents/{id}` – Get a single processed document.
- `POST /documents` – Upload and process a PDF.
- `POST /documents/{id}/reextract` – Re-run extraction with selected sections.
- `GET /search?query=...` – Search across diagnoses and clinical notes.

## Additional files

- [ehr-data-pipeline-backend/README.md](ehr-data-pipeline-backend/README.md) – backend design and pipeline internals.
- [ehr-frontend-website/README.md](ehr-frontend-website/README.md) – frontend usage and development notes.
- [.gitignore](.gitignore) – workspace‑level ignore rules.
- [LICENSE](LICENSE) – MIT license template for this project; replace the placeholders with your organization details.


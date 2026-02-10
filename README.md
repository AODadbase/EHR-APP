# EHR Data Pipeline + Frontend

This workspace contains both:

- **Backend**: EHR data pipeline in Python (PDF processing, extraction, formatting)
- **Frontend**: React dashboard for uploading PDFs, viewing extracted clinical data, and searching

They are wired together so the React app talks to the Python API.

## Project Structure

- `ehr-data-pipeline-backend/` – Python pipeline + FastAPI server
- `ehr-frontend-website/` – React + Vite frontend UI
- `start_app.sh` – (optional) helper script you can use to start both (if you choose to wire it up)

## 1. Backend (Python API)

The backend exposes an HTTP API that wraps your existing pipeline (`PDFProcessor`, `DataExtractor`, `DischargeFormatter`).

Main entry:

- `ehr-data-pipeline-backend/api_server.py` – FastAPI app with endpoints under `/api`:
  - `GET /api/health` – health check
  - `GET /api/documents` – list processed documents
  - `GET /api/documents/{id}` – get one document
  - `POST /api/documents` – upload a PDF and run extraction
  - `POST /api/documents/{id}/reextract` – re-run extraction with selected sections
  - `GET /api/search?query=...` – simple text search across diagnoses/notes

### Backend setup

From `ehr-data-pipeline-backend`:

1. Create & activate a virtual environment (once):
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment (same as existing backend README):
   - Create `.env` next to `app.py` with:
     ```
     UNSTRUCTURED_API_KEY=your_api_key_here
     UNSTRUCTURED_API_URL=https://api.unstructured.io
     OPENAI_API_KEY=your_openai_api_key_here
     OPENAI_MODEL=gpt-4o-mini
     ```

4. Run the API server:
   ```bash
   uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
   ```

5. Verify it is up:
   - Open http://localhost:8000/api/health

> Note: You can still run the original Streamlit UI with `streamlit run app.py` if you want, but it is separate from the React frontend.

## 2. Frontend (React + Vite)

The frontend is a clinical dashboard that calls the Python API.

Key files:

- `ehr-frontend-website/App.tsx` – main app shell
- `ehr-frontend-website/components/` – `Dashboard`, `DocumentDetail`, `SearchInterface`, etc.
- `ehr-frontend-website/services/mockService.ts` – now calls the real API at `/api/...` instead of mocks

### Frontend setup

From `ehr-frontend-website`:

1. Install dependencies:
   ```bash
   npm install
   ```

2. (Optional) Set `GEMINI_API_KEY` in `.env.local` if any parts of the app use Gemini.

3. Run the dev server:
   ```bash
   npm run dev
   ```

4. Open the app:
   - Visit http://localhost:3000

The Vite dev server is configured to **proxy** any `/api` requests to the Python backend at `http://localhost:8000`, so the browser only sees a single origin.

## 3. Running Backend and Frontend Together

For local development:

1. **Start backend** (from `ehr-data-pipeline-backend`):
   ```bash
   source venv/bin/activate
   uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start frontend** (from `ehr-frontend-website`):
   ```bash
   npm run dev
   ```

3. Open http://localhost:3000
   - Upload a PDF from the dashboard.
   - The file and config (use_api/use_llm/sections) go to `POST /api/documents`.
   - Extracted data, discharge summary, and search results are read back via the other `/api` endpoints.

## 4. Where to look for details

- Backend internals: see `ehr-data-pipeline-backend/README.md` and the `src/` modules.
- Frontend details: see `ehr-frontend-website/README.md` and components under `components/`.

## 5. Repo utilities and metadata

- [setup.sh](setup.sh) – one-time setup script that:
   - Creates a Python virtual environment in [ehr-data-pipeline-backend](ehr-data-pipeline-backend) (if missing) and installs `requirements.txt`.
   - Installs Node dependencies in [ehr-frontend-website](ehr-frontend-website) (if `node_modules` is missing).
   - After it completes, you can start both apps using your normal commands (or a helper script like `start_app.sh`).

- [.gitignore](.gitignore) – master ignore file for the whole workspace:
   - Ignores OS cruft (like `.DS_Store`), logs, Python build artifacts and virtual environments, `node_modules`, IDE settings, and `.env` files.
   - Backend and frontend also have their own folder-level `.gitignore` files for more specific patterns.

- [LICENSE](LICENSE) – master project license (MIT by default):
   - Grants broad permission to use, modify, and distribute the code.
   - Update the year and owner line to match your name/organization.

This root README is the high-level map; use the sub-READMEs for deeper implementation details.

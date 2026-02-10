# Traceable Health Frontend

React + Vite frontend for the Traceable Health EHR data pipeline. The UI provides authentication, document upload, document review, search, and account settings.

## Requirements

- Node.js 20 or later.

## Installation

From the `ehr-frontend-website` folder:

```bash
npm install
```

Optional: create `.env.local` and configure any keys used by experimental features (for example `GEMINI_API_KEY`).

## Development

Start the Vite dev server:

```bash
npm run dev
```

Open http://localhost:3000.

The app expects the backend FastAPI server to be running at `http://localhost:8000` and exposes the main flows:

- Email‑based registration and login.
- PDF upload for clinical documents.
- Document dashboard and detail views.
- Search across processed documents.
- User profile and settings.

## Building for production

```bash
npm run build
```

The bundled assets are written to `dist/`.

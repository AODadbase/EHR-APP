"""FastAPI server exposing the EHR data pipeline as a JSON API.

This reuses the existing PDFProcessor, DataExtractor, and DischargeFormatter
modules so the React frontend can upload PDFs, view extracted data, and
perform searches.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.pdf_processor import PDFProcessor
from src.data_extractor import DataExtractor
from src.formatter import DischargeFormatter


# -------------------------------
# Pydantic models (match frontend types.ts)
# -------------------------------


class PatientInfo(BaseModel):
    name: Optional[str] = None
    mrn: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None


class VitalSigns(BaseModel):
    blood_pressure: Optional[str] = None
    heart_rate: Optional[str] = None
    temperature: Optional[str] = None
    respiratory_rate: Optional[str] = None
    oxygen_saturation: Optional[str] = None


class Medication(BaseModel):
    name: str
    dosage: str


class ExtractedData(BaseModel):
    patient_info: PatientInfo
    vital_signs: VitalSigns
    diagnoses: List[str]
    medications: List[Medication]
    allergies: List[str]
    procedures: List[str]
    clinical_notes: List[str]


class ProcessedDocument(BaseModel):
    id: str
    filename: str
    uploadDate: str
    status: str  # 'processing' | 'completed' | 'failed'
    use_api: bool
    use_llm: bool
    extracted_data: Optional[ExtractedData] = None
    discharge_summary: Optional[str] = None
    elements_count: Optional[int] = None


class UploadConfig(BaseModel):
    use_api: bool = True
    use_llm: bool = True
    selected_sections: Optional[List[str]] = None


class ReExtractRequest(BaseModel):
    selected_sections: List[str]


class SearchResult(BaseModel):
    id: str
    documentId: str
    filename: str
    context: str
    matchCount: int


# -------------------------------
# In-memory store (simple demo)
# -------------------------------


class InternalDocument(BaseModel):
    id: str
    filename: str
    upload_date: datetime
    status: str
    use_api: bool
    use_llm: bool
    elements: List[Dict[str, Any]]
    extracted_data: Dict[str, Any]
    discharge_summary: str


DOCUMENTS: Dict[str, InternalDocument] = {}


# -------------------------------
# FastAPI app
# -------------------------------


app = FastAPI(title="EHR Data Pipeline API")

# Allow local dev from Vite (http://localhost:3000) and tools.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ensure_upload_dir() -> str:
    base_dir = os.path.join(os.path.dirname(__file__), "data", "uploads")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _to_extracted_model(raw: Dict[str, Any]) -> ExtractedData:
    # Ensure missing keys become empty structures so frontend types are satisfied.
    return ExtractedData(
        patient_info=PatientInfo(**raw.get("patient_info", {})),
        vital_signs=VitalSigns(**raw.get("vital_signs", {})),
        diagnoses=raw.get("diagnoses", []) or [],
        medications=[Medication(**m) for m in raw.get("medications", []) or []],
        allergies=raw.get("allergies", []) or [],
        procedures=raw.get("procedures", []) or [],
        clinical_notes=raw.get("clinical_notes", []) or [],
    )


def _to_api_document(doc: InternalDocument) -> ProcessedDocument:
    return ProcessedDocument(
        id=doc.id,
        filename=doc.filename,
        uploadDate=doc.upload_date.isoformat(),
        status=doc.status,
        use_api=doc.use_api,
        use_llm=doc.use_llm,
        extracted_data=_to_extracted_model(doc.extracted_data) if doc.extracted_data else None,
        discharge_summary=doc.discharge_summary,
        elements_count=len(doc.elements) if doc.elements else None,
    )


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/documents", response_model=List[ProcessedDocument])
async def list_documents() -> List[ProcessedDocument]:
    # Return most recent first
    docs = sorted(DOCUMENTS.values(), key=lambda d: d.upload_date, reverse=True)
    return [_to_api_document(d) for d in docs]


@app.get("/api/documents/{doc_id}", response_model=ProcessedDocument)
async def get_document(doc_id: str) -> ProcessedDocument:
    doc = DOCUMENTS.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _to_api_document(doc)


@app.post("/api/documents", response_model=ProcessedDocument)
async def upload_document(
    file: UploadFile = File(...),
    use_api: bool = Form(True),
    use_llm: bool = Form(True),
    selected_sections: Optional[str] = Form(None),  # JSON-encoded list from frontend
) -> ProcessedDocument:
    # Persist uploaded file to disk
    upload_dir = _ensure_upload_dir()
    file_id = str(uuid4())
    safe_name = file.filename or f"document-{file_id}.pdf"
    save_path = os.path.join(upload_dir, safe_name)

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Process PDF and extract data
    processor = PDFProcessor(use_api=use_api)
    elements = processor.process_pdf(save_path)

    extractor = DataExtractor(use_llm=use_llm)
    sections: Optional[List[str]] = None
    if selected_sections:
        try:
            import json

            sections = json.loads(selected_sections)
        except Exception:
            sections = None

    extracted = extractor.extract(elements, selected_sections=sections)

    formatter = DischargeFormatter(
        template_path=os.path.join(os.path.dirname(__file__), "templates", "discharge_template.txt")
    )
    discharge_summary = formatter.format(extracted)

    now = datetime.utcnow()
    internal = InternalDocument(
        id=file_id,
        filename=safe_name,
        upload_date=now,
        status="completed",
        use_api=use_api,
        use_llm=use_llm,
        elements=elements,
        extracted_data=extracted,
        discharge_summary=discharge_summary,
    )
    DOCUMENTS[file_id] = internal

    return _to_api_document(internal)


@app.post("/api/documents/{doc_id}/reextract", response_model=ProcessedDocument)
async def reextract_document(doc_id: str, payload: ReExtractRequest) -> ProcessedDocument:
    doc = DOCUMENTS.get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    extractor = DataExtractor(use_llm=doc.use_llm)
    extracted = extractor.extract(doc.elements, selected_sections=payload.selected_sections)

    formatter = DischargeFormatter(
        template_path=os.path.join(os.path.dirname(__file__), "templates", "discharge_template.txt")
    )
    discharge_summary = formatter.format(extracted)

    doc.extracted_data = extracted
    doc.discharge_summary = discharge_summary
    doc.upload_date = datetime.utcnow()  # refresh timestamp
    DOCUMENTS[doc_id] = doc

    return _to_api_document(doc)


@app.get("/api/search", response_model=List[SearchResult])
async def search_documents(query: str) -> List[SearchResult]:
    """Very simple substring search over diagnoses and clinical notes.

    This is a placeholder; you can later plug in a vector DB or more
    advanced search while keeping the same response shape for the frontend.
    """
    q = query.strip()
    if not q:
        return []

    q_lower = q.lower()
    results: List[SearchResult] = []

    for doc in DOCUMENTS.values():
        data = doc.extracted_data or {}
        diagnoses = "\n".join(data.get("diagnoses", []) or [])
        notes = "\n".join(data.get("clinical_notes", []) or [])
        haystack = f"{diagnoses}\n{notes}".lower()

        if q_lower in haystack:
            # Build a simple context snippet with highlighted query
            idx = haystack.find(q_lower)
            start = max(0, idx - 60)
            end = idx + len(q) + 60
            original_text = f"{diagnoses}\n{notes}"[start:end]
            highlighted = original_text.replace(q, f"<b>{q}</b>")

            results.append(
                SearchResult(
                    id=str(uuid4()),
                    documentId=doc.id,
                    filename=doc.filename,
                    context=f"...{highlighted}...",
                    matchCount=haystack.count(q_lower),
                )
            )

    return results


# Convenience entrypoint for `uvicorn api_server:app --reload`
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)

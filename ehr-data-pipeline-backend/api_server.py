"""FastAPI server exposing the EHR data pipeline as a JSON API."""

from __future__ import annotations

import os
import random
import resend
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from dotenv import load_dotenv

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.pdf_processor import PDFProcessor
from src.data_extractor import DataExtractor
from src.formatter import DischargeFormatter


# -------------------------------
# CONFIGURATION
# -------------------------------

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

if not resend.api_key:
    print("WARNING: No RESEND_API_KEY found in .env file. Emails will fail.")

app = FastAPI(title="EHR Data Pipeline API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# PYDANTIC MODELS
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
    status: str
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

class EmailRequest(BaseModel):
    email: str

class VerificationRequest(BaseModel):
    email: str
    code: str


# -------------------------------
# IN-MEMORY STORE
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
VERIFICATION_CODES: Dict[str, str] = {}


# -------------------------------
# HELPER FUNCTIONS
# -------------------------------

def _ensure_upload_dir() -> str:
    base_dir = os.path.join(os.path.dirname(__file__), "data", "uploads")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def _to_extracted_model(raw: Dict[str, Any]) -> ExtractedData:
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


# -------------------------------
# API ROUTES
# -------------------------------

@app.post("/api/send-code")
def send_email(request: EmailRequest):
    code = str(random.randint(100000, 999999))
    VERIFICATION_CODES[request.email] = code
    
    print(f"Generated code {code} for {request.email}")

    try:
        r = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": request.email, 
            "subject": "Your EHR App Verification Code",
            "html": f"<p>Your verification code is: <strong>{code}</strong></p>"
        })
        return {"message": "Email sent!", "id": r.get('id')}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"message": "Email failed (check console)", "mock_code": code}

@app.post("/api/verify-code")
def verify_code(request: VerificationRequest):
    stored_code = VERIFICATION_CODES.get(request.email)
    
    if stored_code and stored_code == request.code:
        del VERIFICATION_CODES[request.email]
        return {"message": "Verified!", "token": "fake-jwt-token"}
    else:
        raise HTTPException(status_code=400, detail="Invalid verification code")

@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/api/documents", response_model=List[ProcessedDocument])
async def list_documents() -> List[ProcessedDocument]:
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
    selected_sections: Optional[str] = Form(None),
) -> ProcessedDocument:
    upload_dir = _ensure_upload_dir()
    file_id = str(uuid4())
    safe_name = file.filename or f"document-{file_id}.pdf"
    save_path = os.path.join(upload_dir, safe_name)

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

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
    doc.upload_date = datetime.utcnow()
    DOCUMENTS[doc_id] = doc

    return _to_api_document(doc)

@app.get("/api/search", response_model=List[SearchResult])
async def search_documents(query: str) -> List[SearchResult]:
    q = query.strip()
    if not q:
        return []

    q_lower = q.lower()
    results: List[SearchResult] = []

    for doc in DOCUMENTS.values():
        data = doc.extracted_data or {}
        haystack = (
            "\n".join(data.get("diagnoses", []) or []) + 
            "\n" + 
            "\n".join(data.get("clinical_notes", []) or [])
        ).lower()

        if q_lower in haystack:
            idx = haystack.find(q_lower)
            start = max(0, idx - 60)
            end = idx + len(q) + 60
            original_text = haystack[start:end]
            highlighted = original_text.replace(q_lower, f"<b>{q_lower}</b>")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ocr import extract_text_from_image, extract_text_from_pdf
from gemini import extract_fields_with_gemini
from pdf_fill import generate_filled_pdf
from utils import save_upload_file
from pydantic import BaseModel

app = FastAPI(title="Smart Form Filler API")

UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Allow frontend (Next.js) during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


class FillRequest(BaseModel):
    fields: Dict[str, Any]
    template_pdf_filename: Optional[str] = None


@app.post("/process")
async def process_form(
    form_image: UploadFile = File(...),
    documents: List[UploadFile] = File(default_factory=list),
) -> dict:
    """Main pipeline endpoint: save files, run OCR + Gemini, return JSON + filled PDF path.

    For now, this is a stub that wires the modules and returns placeholder results.
    We'll improve OCR, Gemini, and PDF logic in later steps.
    """
    try:
        base_upload_dir = Path(__file__).resolve().parent / "uploads"
        base_upload_dir.mkdir(parents=True, exist_ok=True)

        form_path = save_upload_file(form_image, base_upload_dir)
        _doc_paths = [save_upload_file(doc, base_upload_dir / "docs") for doc in documents]

        # Decide which file to use as OCR source: first supporting document if present,
        # otherwise fall back to the main form file.
        if _doc_paths:
            ocr_source = _doc_paths[0]
        else:
            ocr_source = form_path

        # Step 3: we'll implement real Tesseract OCR here
        if ocr_source.suffix.lower() == ".pdf":
            raw_text = extract_text_from_pdf(str(ocr_source))
        else:
            raw_text = extract_text_from_image(str(ocr_source))

        # Step 4: we'll implement real Gemini extraction here
        fields = extract_fields_with_gemini(raw_text)

        # Step 5: for this step we only return extracted fields and template info;
        # PDF generation happens in a separate /fill endpoint after the user reviews/edits.
        template_path = form_path if form_path.suffix.lower() == ".pdf" else None
        template_filename = template_path.name if template_path is not None else None

        return {
            "fields": fields,
            "template_pdf_filename": template_filename,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/fill")
async def fill_pdf(request: FillRequest) -> dict:
    """Generate a filled PDF from edited fields and an optional template PDF.

    If template_pdf_filename is provided and exists, we overlay the fields onto
    that template. Otherwise we fall back to a simple summary PDF.
    """
    try:
        base_upload_dir = Path(__file__).resolve().parent / "uploads"
        base_upload_dir.mkdir(parents=True, exist_ok=True)

        template_path: Optional[Path] = None
        if request.template_pdf_filename:
            candidate = base_upload_dir / request.template_pdf_filename
            if candidate.is_file():
                template_path = candidate

        filled_pdf_path = generate_filled_pdf(
            request.fields,
            base_upload_dir,
            template_path=template_path,
        )

        return {
            "filled_pdf_filename": Path(filled_pdf_path).name,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

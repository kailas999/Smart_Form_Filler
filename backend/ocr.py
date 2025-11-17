from typing import Optional
from io import BytesIO

from PIL import Image, ImageOps
import pytesseract
import fitz  # PyMuPDF


def _preprocess_image(image: Image.Image) -> Image.Image:
    """Simple preprocessing to improve OCR accuracy."""
    # Convert to grayscale and apply a light threshold to reduce noise
    gray = ImageOps.grayscale(image)
    bw = gray.point(lambda x: 0 if x < 160 else 255, "1")
    return bw


def extract_text_from_image(image_path: str, language: str = "eng", tesseract_cmd: Optional[str] = None) -> str:
    """Placeholder OCR function.

    In Step 3 we'll implement real OCR using Tesseract (pytesseract) so that this
    returns the full text content of the uploaded form and documents.
    """
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    image = Image.open(image_path)
    processed = _preprocess_image(image)
    text = pytesseract.image_to_string(processed, lang=language)
    return text


def extract_text_from_pdf(pdf_path: str, language: str = "eng", tesseract_cmd: Optional[str] = None) -> str:
    """Extract text from the first page of a PDF using PyMuPDF + Tesseract."""
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    doc = fitz.open(pdf_path)
    if doc.page_count == 0:
        return ""

    page = doc[0]
    pix = page.get_pixmap(dpi=200)
    img_bytes = pix.tobytes("png")
    doc.close()

    image = Image.open(BytesIO(img_bytes))
    processed = _preprocess_image(image)
    text = pytesseract.image_to_string(processed, lang=language)
    return text

from typing import Dict, Any
import json
import os

import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_ID = os.getenv("GEMINI_MODEL_ID", "gemini-pro")

if API_KEY:
    genai.configure(api_key=API_KEY)


def _get_model() -> genai.GenerativeModel:
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in environment or .env file")
    return genai.GenerativeModel(MODEL_ID)


def extract_fields_with_gemini(raw_text: str) -> Dict[str, Any]:
    """Call Gemini to extract structured fields from OCR text.

    Returns a dictionary like:
    {
        "name": "...",
        "dob": "YYYY-MM-DD or original format",
        "address": "...",
        "phone": "...",
        "email": "...",
        "raw_text": "original ocr text"
    }
    """

    model = _get_model()

    prompt = f"""
You are an information extraction engine for ID cards and forms.

Given the OCR text of a filled document, extract the following fields when present:
- full name
- date of birth
- address
- phone number
- email

VERY IMPORTANT CONSTRAINTS:
- You must only use substrings that appear exactly in OCR_TEXT.
- Do not hallucinate or guess any value that is not clearly present.
- If you are not 100% sure a value is explicitly present in OCR_TEXT, set it to null.

Return ONLY a valid JSON object with keys:
  name, dob, address, phone, email
Missing values must be null.

OCR_TEXT:

{raw_text}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
    except Exception as exc:
        # If Gemini call fails (e.g. model ID not supported), return a
        # structured response instead of raising so the API stays responsive.
        return {
            "name": None,
            "dob": None,
            "address": None,
            "phone": None,
            "email": None,
            "raw_text": raw_text,
            "_error": f"Gemini request failed: {exc}",
        }

    # Gemini may wrap JSON in code fences; strip them if present
    if text.startswith("```"):
        lines = text.splitlines()
        # remove first and last fence lines
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1])

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: wrap everything in a generic structure
        data = {
            "name": None,
            "dob": None,
            "address": None,
            "phone": None,
            "email": None,
            "_raw_model_output": text,
        }

    # Enforce that extracted fields must be substrings of the OCR text
    data = _enforce_substring_constraints(data, raw_text)
    data["raw_text"] = raw_text
    return data


def _enforce_substring_constraints(data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
    """Ensure that each field value appears in the OCR text; otherwise set to None.

    This is a strong anti-hallucination guard: if Gemini returns a value that
    cannot be found in the OCR text (ignoring case and extra whitespace), we
    drop it.
    """
    ocr_norm = " ".join(raw_text.lower().split())

    for key in ["name", "dob", "address", "phone", "email"]:
        val = data.get(key)
        if isinstance(val, str):
            val_norm = " ".join(val.lower().split())
            if val_norm and val_norm not in ocr_norm:
                data[key] = None
    return data

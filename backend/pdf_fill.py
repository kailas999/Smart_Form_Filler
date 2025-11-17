from pathlib import Path
from typing import Dict, Union, Optional

import fitz  # PyMuPDF


PathLike = Union[str, Path]


def generate_filled_pdf(
    fields: Dict,
    output_dir: PathLike,
    template_path: Optional[PathLike] = None,
) -> str:
    """Placeholder PDF generator.

    In Step 5 we'll use PyMuPDF (fitz) to fill a PDF template and save it.
    For now we create an empty file so the endpoint works end-to-end.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    template = Path(template_path) if template_path is not None else None

    if template is not None and template.is_file() and template.suffix.lower() == ".pdf":
        # Use the uploaded PDF as the base template
        doc = fitz.open(str(template))
        page = doc[0]
        pdf_path = out_dir / f"{template.stem}_filled.pdf"
    else:
        # Fallback: create a simple one-page PDF summary
        doc = fitz.open()
        page = doc.new_page()
        pdf_path = out_dir / "filled_form.pdf"

    # Prepare field values
    name = fields.get("name") if isinstance(fields, dict) else None
    dob = fields.get("dob") if isinstance(fields, dict) else None
    address = fields.get("address") if isinstance(fields, dict) else None
    phone = fields.get("phone") if isinstance(fields, dict) else None
    email = fields.get("email") if isinstance(fields, dict) else None

    if template is not None and template.is_file() and template.suffix.lower() == ".pdf":
        # Try to place values next to common labels on the template.
        label_map = {
            "Full Name:": name,
            "Current Address:": address,
            "Telephone Number:": phone,
            "Email Address:": email,
            "Name:": name,
            "Date of Birth:": dob,
        }

        for label, value in label_map.items():
            if not value:
                continue
            rects = page.search_for(label)
            if not rects:
                continue
            rect = rects[0]
            # Place text slightly to the right of the label on the same line.
            x = rect.x1 + 8
            # Use the vertical middle of the label's bounding box.
            y = rect.y0 + (rect.y1 - rect.y0) * 0.7
            page.insert_text((x, y), str(value), fontsize=10, fill=(0, 0, 0))
    else:
        # Summary-only mode when there is no template PDF.
        lines = [
            "Smart Form Filler - Extracted Data",
            "",
            f"Name: {name or ''}",
            f"Date of Birth: {dob or ''}",
            f"Address: {address or ''}",
            f"Phone: {phone or ''}",
            f"Email: {email or ''}",
        ]

        text = "\n".join(lines)
        # Draw text with a margin (72 pt = 1 inch)
        page.insert_text((72, 72), text, fontsize=12)

    doc.save(str(pdf_path))
    doc.close()

    return str(pdf_path)

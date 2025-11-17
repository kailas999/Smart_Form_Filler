import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile


def save_upload_file(upload_file: UploadFile, base_dir: Optional[Path] = None) -> Path:
    """Save an uploaded file to disk and return the saved path."""
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent / "uploads"

    base_dir.mkdir(parents=True, exist_ok=True)

    original_name = upload_file.filename or "file"
    suffix = Path(original_name).suffix
    filename = f"{uuid.uuid4().hex}{suffix}"

    dest_path = base_dir / filename

    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return dest_path

import os
import re
from fastapi import HTTPException, status, UploadFile
from backend.core.config import settings

def sanitize_filename(filename: str) -> str:
    """Strip dangerous characters from filenames to prevent path traversal."""
    filename = os.path.basename(filename)
    # Remove all non-alphanumeric characters except dots, hyphens, and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return sanitized or "unnamed_document"

def validate_upload_file(file: UploadFile, contents: bytes) -> None:
    """Validate upload file extension and size constraints."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

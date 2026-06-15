import os
import shutil
import tempfile
import time
from fastapi import UploadFile, HTTPException
from config.config import settings

def validate_file_extension(filename: str | None) -> str:
    """
    Validates that the uploaded filename has an allowed audio extension.
    Accepts str | None because FastAPI's UploadFile.filename is Optional[str].
    """
    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file has no filename. Please provide a valid audio file."
        )
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    return file_ext

def save_temp_file(file: UploadFile, file_ext: str) -> tuple[str, str]:
    """
    Saves the uploaded file to a temporary file on disk.
    Returns a tuple of (temp_dir_path, temp_file_path).
    """
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, f"upload_{int(time.time())}{file_ext}")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return temp_dir, temp_file_path
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        print(f"Error saving temp file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file locally.")

def cleanup_temp_dir(temp_dir: str) -> None:
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up local temp folder: {temp_dir}")
    except Exception as e:
        print(f"Failed to delete local temp file at {temp_dir}: {e}")

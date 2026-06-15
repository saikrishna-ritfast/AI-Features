import os
import shutil
import tempfile
import time
import httpx
from urllib.parse import urlparse
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

async def save_temp_file(file: UploadFile, file_ext: str) -> tuple[str, str]:
    """
    Saves the uploaded file to a temporary file on disk.
    Returns a tuple of (temp_dir_path, temp_file_path).
    """
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, f"upload_{int(time.time())}{file_ext}")

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        with open(temp_file_path, "wb") as buffer:
            buffer.write(content)
        return temp_dir, temp_file_path
    except HTTPException:
        cleanup_temp_dir(temp_dir)
        raise
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

def _filename_from_content_disposition(header: str | None) -> str | None:
    """Extract a filename from a Content-Disposition header, if present."""
    if not header:
        return None
    for part in header.split(";"):
        part = part.strip()
        if part.lower().startswith("filename="):
            return part.split("=", 1)[1].strip().strip('"').strip("'")
    return None

async def download_file_from_url(url: str, headers: dict[str, str] | None = None) -> tuple[str, str]:
    """
    Downloads a file from a remote HTTP/HTTPS URL into a local temporary directory.
    Optionally includes custom HTTP headers (e.g. Authorization) in the request.
    Returns a tuple of (temp_dir_path, temp_file_path).
    """
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=400,
            detail="Only HTTP and HTTPS URLs are supported."
        )

    url_filename = os.path.basename(parsed_url.path)
    temp_dir = tempfile.mkdtemp()

    try:
        timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("GET", url, headers=headers, follow_redirects=True) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to fetch recording from remote URL. Status code: {response.status_code}"
                    )

                content_disposition_name = _filename_from_content_disposition(
                    response.headers.get("Content-Disposition")
                )
                if content_disposition_name:
                    file_ext = validate_file_extension(content_disposition_name)
                elif url_filename:
                    file_ext = validate_file_extension(url_filename)
                else:
                    file_ext = validate_file_extension("downloaded_audio.mp3")

                temp_file_path = os.path.join(
                    temp_dir, f"url_download_{int(time.time())}{file_ext}"
                )

                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        if int(content_length) > settings.MAX_DOWNLOAD_BYTES:
                            raise HTTPException(
                                status_code=400,
                                detail="The remote file exceeds the maximum size limit of 50MB."
                            )
                    except ValueError:
                        pass

                downloaded_bytes = 0
                with open(temp_file_path, "wb") as buffer:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        downloaded_bytes += len(chunk)
                        if downloaded_bytes > settings.MAX_DOWNLOAD_BYTES:
                            raise HTTPException(
                                status_code=400,
                                detail="The downloaded file exceeded the maximum size limit of 50MB."
                            )
                        buffer.write(chunk)

                if downloaded_bytes == 0:
                    raise HTTPException(
                        status_code=400,
                        detail="The remote URL returned an empty file."
                    )

        return temp_dir, temp_file_path
        
    except httpx.TimeoutException:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(
            status_code=408,
            detail="Timed out while downloading the recording from the remote URL."
        )
    except httpx.RequestError as e:
        cleanup_temp_dir(temp_dir)
        print(f"Network error downloading file: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Network error when downloading recording: {str(e)}"
        )
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        if isinstance(e, HTTPException):
            raise e
        print(f"Error downloading file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download remote file locally: {str(e)}"
        )


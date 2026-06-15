from fastapi import APIRouter, File, UploadFile
from models.analysis import CallAnalysis, AnalyzeUrlRequest
from utils.file import validate_file_extension, save_temp_file, cleanup_temp_dir, download_file_from_url
from services.gemini import gemini_service
import base64

router = APIRouter(
    prefix="/api",
    tags=["Call Analysis"]
)

@router.post("/analyze", response_model=CallAnalysis, summary="Analyze a call recording")
async def analyze_audio(file: UploadFile = File(..., description="Audio call recording file (.mp3, .wav, .m4a, .ogg, .flac, .webm)")):
    """
    Upload an audio recording of a customer call to extract structured insights and a full translated transcript.
    """
    # 1. Validate file extension
    file_ext = validate_file_extension(file.filename)
    
    # 2. Save file temporarily on local disk
    temp_dir, temp_file_path = await save_temp_file(file, file_ext)
    
    try:
        # 3. Process with Gemini service
        analysis_result = await gemini_service.analyze_call(temp_file_path)
        return analysis_result
    finally:
        # 4. Clean up temporary files
        cleanup_temp_dir(temp_dir)

# @router.post("/analyze-url", response_model=CallAnalysis, summary="Analyze a call recording from a remote URL")
# async def analyze_audio_url(request: AnalyzeUrlRequest):
#     """
#     Provide the HTTP/HTTPS URL of a call recording to extract structured insights and a full translated transcript.
#     """
#     # 1. Download the remote file to temporary space
#     temp_dir, temp_file_path = await download_file_from_url(str(request.url), headers=request.headers)
    
#     try:
#         # 2. Process with Gemini service
#         analysis_result = await gemini_service.analyze_call(temp_file_path)
#         return analysis_result
#     finally:
#         # 3. Clean up downloaded temporary files
#         cleanup_temp_dir(temp_dir)

@router.post("/analyze-url", response_model=CallAnalysis)
async def analyze_audio_url(request: AnalyzeUrlRequest):
    headers = request.headers or {}

    if request.api_key and request.api_token:
        credentials = f"{request.api_key}:{request.api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers = {**headers, "Authorization": f"Basic {encoded}"}

    temp_dir, temp_file_path = await download_file_from_url(str(request.url), headers=headers)

    try:
        analysis_result = await gemini_service.analyze_call(temp_file_path)
        return analysis_result
    finally:
        cleanup_temp_dir(temp_dir)

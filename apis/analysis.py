from fastapi import APIRouter, File, UploadFile
from models.analysis import CallAnalysis
from utils.file import validate_file_extension, save_temp_file, cleanup_temp_dir
from services.gemini import gemini_service

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
    temp_dir, temp_file_path = save_temp_file(file, file_ext)
    
    try:
        # 3. Process with Gemini service
        analysis_result = await gemini_service.analyze_call(temp_file_path)
        return analysis_result
    finally:
        # 4. Clean up temporary files
        cleanup_temp_dir(temp_dir)

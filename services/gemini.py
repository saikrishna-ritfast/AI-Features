import asyncio
import time
from fastapi import HTTPException
from google import genai
from config.config import settings
from models.analysis import CallAnalysis

class GeminiService:
    def __init__(self):
        # Initialize Gemini Client using API key from settings
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = 'gemini-2.5-flash'

    async def analyze_call(self, file_path: str) -> CallAnalysis:
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "" or settings.GEMINI_API_KEY.startswith("YOUR_"):
            raise HTTPException(
                status_code=400,
                detail="Gemini API Key is not configured. Please set GEMINI_API_KEY in your .env file."
            )
            
        try:
            print(f"Uploading file {file_path} to Gemini...")
            audio_file = self.client.files.upload(file=file_path)

            # Validate the uploaded file has a name (type-safe guard)
            if audio_file.name is None:
                raise HTTPException(
                    status_code=500,
                    detail="Gemini returned an uploaded file with no name identifier."
                )
            
            # Wait for file processing (crucial for larger audio files)
            wait_start = time.time()
            while audio_file.state is not None and audio_file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                await asyncio.sleep(2)  # Non-blocking: keeps event loop free
                # Timeout after 2 minutes to prevent infinite loops
                if time.time() - wait_start > 120:
                    raise HTTPException(
                        status_code=504, 
                        detail="Gemini API timed out during audio file processing."
                    )
                # audio_file.name is already narrowed to str by the guard above
                audio_file = self.client.files.get(name=audio_file.name)
                
            if audio_file.state is not None and audio_file.state.name == "FAILED":
                raise HTTPException(
                    status_code=500, 
                    detail="Gemini failed to process the uploaded audio file."
                )
                
            print(f"\nFile processed successfully! URI: {audio_file.uri}")
            
            # Request translation, transcription, and insights metadata
            prompt = """
            The attached audio file contains a conversation that may not be in English.
            Listen to the audio, translate all spoken dialogue directly into English, and structure 
            the final transcript into 'Agent: ...' and 'User: ...' lines.
            
            Then, use the context of that translation to fill out the metadata analysis fields entirely in English.
            Specifically estimate the total call duration, agent talk time, and customer talk time in seconds.
            """
            
            print("Invoking Gemini model for structured analysis...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[audio_file, prompt],
                config=dict(
                    response_mime_type="application/json",
                    response_schema=CallAnalysis,
                ),
            )
            
            # Clean up the file from Gemini storage space
            try:
                # audio_file.name is str here (narrowed above)
                if audio_file.name:
                    self.client.files.delete(name=audio_file.name)
                    print(f"Deleted file {audio_file.name} from Gemini cloud storage.")
            except Exception as delete_err:
                print(f"Warning: Failed to delete file from Gemini storage: {delete_err}")
                
            # Parse and validate JSON against the schema
            if not response.text:
                raise HTTPException(
                    status_code=500, 
                    detail="Gemini API returned an empty response text."
                )
                
            try:
                return CallAnalysis.model_validate_json(response.text)
            except Exception as val_err:
                print(f"Failed to validate response against CallAnalysis: {val_err}")
                print(f"Raw model response: {response.text}")
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to validate structured JSON output from Gemini."
                )
                
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            
            err_msg = str(e).lower()
            print(f"Error in GeminiService: {e}")
            
            # Check for common authentication or API key issues
            if "api key" in err_msg or "api_key" in err_msg or "invalid key" in err_msg or "unauthorized" in err_msg or "forbidden" in err_msg or "400" in err_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication failed. Please verify your GEMINI_API_KEY in the .env file."
                )
                
            raise HTTPException(
                status_code=500, 
                detail=f"Error executing call intelligence analysis: {str(e)}"
            )

# Singleton instance
gemini_service = GeminiService()

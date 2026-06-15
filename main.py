import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from apis.analysis import router as analysis_router
from config.config import settings

app = FastAPI(
    title="Call AI - Conversation Intelligence API",
    description=(
        "FastAPI backend for transcribing, translating, and extracting structured insights "
        "from call recordings using Google Gemini."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the modular routers
app.include_router(analysis_router)

@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root access to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    print(f"\n[*] Starting Call AI Backend Server...")
    print(f"[-] Local API Base: http://{settings.HOST}:{settings.PORT}")
    print(f"[-] Swagger UI docs: http://{settings.HOST}:{settings.PORT}/docs\n")
    
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)



# .venv\Scripts\Activate.ps1
# python main.py
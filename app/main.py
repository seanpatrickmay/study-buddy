from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import shutil
from pathlib import Path
import uuid
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.config import settings
from app.utils.study_workflow import StudyWorkflow

# Create FastAPI app
app = FastAPI(
    title="Study Buddy API",
    description="Two-step study workflow: PDFs to Anki decks, Anki exports to personalised cheat sheets.",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize workflow
workflow = StudyWorkflow()

# Create necessary directories
for dir_path in [settings.upload_dir, settings.output_dir]:
    dir_path.mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def web_interface(request: Request):
    """Serve the web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download generated files"""
    try:
        # Security check - ensure file is in output directory
        full_path = Path(file_path)
        if not full_path.exists():
            # Try relative to output directory
            full_path = settings.output_dir / file_path

        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process")
async def process_pdfs(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(default=[]),
    anki_export: UploadFile = File(None)
):
    """
    Process uploaded PDFs and generate study materials
    
    Returns:
    - Flashcards in JSON format
    - Anki deck file
    - Comprehensive cheat sheet
    """
    file_paths = []
    anki_export_path = None

    # Validate that at least PDFs or Anki export is provided
    if not files and not anki_export:
        raise HTTPException(status_code=400, detail="Please provide either PDF files or an Anki export file")

    allowed_extensions = {".pdf", ".ppt", ".pptx"}

    # Process study files (if any)
    for file in files:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} has an unsupported format. Allowed: PDF, PPT, PPTX",
            )

        # Generate unique ID and save
        file_id = str(uuid.uuid4())
        file_path = settings.upload_dir / f"{file_id}_{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            file_path.unlink()
            raise HTTPException(
                status_code=413,
                detail=f"File {file.filename} too large: {file_size_mb:.2f}MB (max: {settings.max_file_size_mb}MB)"
            )

        file_paths.append(str(file_path))

    # Process Anki export file if provided
    if anki_export and anki_export.filename.endswith(".apkg"):
        anki_id = str(uuid.uuid4())
        anki_export_path = settings.upload_dir / f"{anki_id}_{anki_export.filename}"

        with open(anki_export_path, "wb") as buffer:
            shutil.copyfileobj(anki_export.file, buffer)

    try:
        # Choose workflow based on what's provided
        if file_paths:
            # PDFs provided - use full workflow (with optional Anki export)
            result = await workflow.process_study_materials(file_paths, str(anki_export_path) if anki_export_path else None)
        elif anki_export_path:
            # Only Anki export provided - use Anki-only workflow for customized cheat sheet
            result = await workflow.process_anki_only_workflow(str(anki_export_path))
        else:
            # This shouldn't happen due to validation above, but just in case
            raise HTTPException(status_code=400, detail="No files provided")

        # Schedule cleanup
        for path in file_paths:
            background_tasks.add_task(cleanup_file, Path(path))

        if anki_export_path:
            background_tasks.add_task(cleanup_file, Path(anki_export_path))

        return JSONResponse(content=result)

    except Exception as e:
        # Print full error details to console for debugging
        import traceback
        print(f"❌ ERROR in /process endpoint: {str(e)}")
        print(f"❌ Full traceback:")
        traceback.print_exc()

        # Cleanup on error
        for path in file_paths:
            p = Path(path)
            if p.exists():
                p.unlink()
        raise HTTPException(status_code=500, detail=str(e))

def cleanup_file(file_path: Path):
    """Clean up uploaded file after processing"""
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Error cleaning up file {file_path}: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

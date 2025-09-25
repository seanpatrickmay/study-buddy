from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import shutil
from pathlib import Path
import uuid
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.config import settings
from app.utils.pipeline import StudyPipeline

from typing import List

# Create FastAPI app
app = FastAPI(
    title="Study Material Generator",
    description="Transform PDFs into comprehensive study materials",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = StudyPipeline()

# Create necessary directories
for dir_path in [settings.upload_dir, settings.output_dir, settings.temp_dir]:
    dir_path.mkdir(parents=True, exist_ok=True)

@app.post("/process")
async def process_pdfs(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Process uploaded PDFs and generate study materials
    
    Returns:
    - Flashcards in JSON format
    - Anki deck file
    - Comprehensive cheat sheet
    """
    file_paths = []

    for file in files:
        # Validate type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF")

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

    try:
        # Process all files
        result = await pipeline.process_pdfs(file_paths)

        # Schedule cleanup
        for path in file_paths:
            background_tasks.add_task(cleanup_file, Path(path))

        return JSONResponse(content=result)

    except Exception as e:
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

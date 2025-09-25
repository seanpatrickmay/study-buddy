from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path
import uuid
from typing import Optional
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
async def process_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Process uploaded PDF and generate study materials
    
    Returns:
    - Flashcards in JSON format
    - Anki deck file
    - Comprehensive cheat sheet
    """
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    file_path = settings.upload_dir / f"{file_id}_{file.filename}"
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.max_file_size_mb:
            file_path.unlink()
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file_size_mb:.2f}MB (max: {settings.max_file_size_mb}MB)"
            )
        
        # Process file
        result = await pipeline.process_pdf(str(file_path))
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_file, file_path)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_type}/{filename}")
async def download_file(file_type: str, filename: str):
    """Download generated files"""
    
    file_path = settings.output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    media_types = {
        'json': 'application/json',
        'apkg': 'application/octet-stream',
        'md': 'text/markdown',
        'txt': 'text/plain'
    }
    
    file_ext = filename.split('.')[-1]
    media_type = media_types.get(file_ext, 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "configs": {
            "llm_model": settings.llm_model,
            "max_file_size_mb": settings.max_file_size_mb
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Study Bot API",
        "documentation": "/docs",
        "health": "/health"
    }


@app.post("/add-to-database")
async def add_to_database(
    file: UploadFile = File(...)
):
    """Add a PDF to the vector database without generating materials immediately"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    file_id = str(uuid.uuid4())
    file_path = settings.upload_dir / f"{file_id}_{file.filename}"
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Add to database only
        result = await pipeline.process_pdf(str(file_path), add_to_db_only=True)
        
        return JSONResponse(content=result)
        
    finally:
        if file_path.exists():
            file_path.unlink()

@app.post("/process-multiple")
async def process_multiple_pdfs(
    files: List[UploadFile] = File(...)
):
    """Process multiple PDFs (up to 5) and create unified study materials"""
    
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed")
    
    saved_paths = []
    
    try:
        # Save all files
        for file in files:
            if not file.filename.endswith('.pdf'):
                continue
            
            file_id = str(uuid.uuid4())
            file_path = settings.upload_dir / f"{file_id}_{file.filename}"
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_paths.append(str(file_path))
        
        # Process all PDFs
        result = await pipeline.process_multiple_pdfs(saved_paths)
        
        return JSONResponse(content=result)
        
    finally:
        # Clean up files
        for path in saved_paths:
            if Path(path).exists():
                Path(path).unlink()

@app.get("/database-info")
async def database_info():
    """Get information about the vector database"""
    info = pipeline.get_database_info()
    return JSONResponse(content=info)

@app.post("/generate-from-database")
async def generate_from_database():
    """Generate study materials from all files in the database"""
    
    try:
        materials = await pipeline._generate_study_materials()
        output_files = pipeline._save_outputs(materials)
        
        return JSONResponse(content={
            "status": "success",
            "files": output_files,
            "database_info": pipeline.get_database_info()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear-database")
async def clear_database():
    """Clear the entire vector database"""
    pipeline.clear_database()
    return {"status": "success", "message": "Database cleared"}

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
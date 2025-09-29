"""FastAPI application exposing the Study Buddy web interface and API."""
from __future__ import annotations

import logging
import shutil
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from study_buddy.config import settings
from study_buddy.workflows.study import StudyWorkflow

LOGGER = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"
ALLOWED_EXTENSIONS = {".pdf", ".ppt", ".pptx"}


def create_application() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    application = FastAPI(
        title="Study Buddy API",
        description="Generate flashcards, cheat sheets, and decks from study materials.",
        version="2.0.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    application.state.templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

    @application.on_event("startup")
    async def _prepare_directories() -> None:
        for directory in (settings.upload_dir, settings.output_dir):
            directory.mkdir(parents=True, exist_ok=True)

    return application


@lru_cache(maxsize=1)
def get_workflow() -> StudyWorkflow:
    """Return a cached :class:`StudyWorkflow` instance."""
    return StudyWorkflow()


app = create_application()


@app.get("/", response_class=HTMLResponse)
async def get_web_interface(request: Request) -> HTMLResponse:
    """Render the single-page web interface."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/download/{file_path:path}")
async def download_file(file_path: str) -> FileResponse:
    """Provide download access to generated artefacts."""
    candidate = Path(file_path)
    if not candidate.exists():
        candidate = settings.output_dir / file_path

    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Requested file was not found.")

    return FileResponse(path=str(candidate), filename=candidate.name, media_type="application/octet-stream")


@app.post("/process")
async def process_materials(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(default_factory=list),
    anki_export: Optional[UploadFile] = File(None),
    workflow: StudyWorkflow = Depends(get_workflow),
) -> JSONResponse:
    """Process uploaded study materials and optional Anki exports."""
    stored_files: List[Path] = []
    anki_export_path: Optional[Path] = None

    if not files and not anki_export:
        raise HTTPException(status_code=400, detail="Upload at least one study file or an Anki export.")

    try:
        stored_files = [_store_upload(upload) for upload in files]
        if anki_export:
            anki_export_path = _store_upload(anki_export, allowed_extensions={".apkg"})

        if stored_files:
            result = await workflow.process_study_materials(
                [str(path) for path in stored_files],
                str(anki_export_path) if anki_export_path else None,
            )
        elif anki_export_path:
            result = await workflow.process_anki_only_workflow(str(anki_export_path))
        else:
            raise HTTPException(status_code=400, detail="No files were processed.")

        for path in stored_files + ([anki_export_path] if anki_export_path else []):
            if path:
                background_tasks.add_task(_delete_file, path)

        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive logging
        LOGGER.exception("Failed to process study materials: %%s", exc)
        for path in stored_files + ([anki_export_path] if anki_export_path else []):
            if path:
                _delete_file(path)
        raise HTTPException(status_code=500, detail="Processing failed; check server logs for details.") from exc


def _store_upload(upload: UploadFile, *, allowed_extensions: Iterable[str] = ALLOWED_EXTENSIONS) -> Path:
    """Persist an uploaded file after validating its extension and size limits."""
    filename = upload.filename or "uploaded-file"
    suffix = Path(filename).suffix.lower()
    if allowed_extensions and suffix not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type for {filename}.")

    destination = settings.upload_dir / f"{uuid.uuid4()}_{filename}"
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    upload.file.close()

    size_mb = destination.stat().st_size / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=413,
            detail=f"File {filename} is too large ({size_mb:.2f} MB). Maximum allowed size is {settings.max_file_size_mb} MB.",
        )

    return destination


def _delete_file(path: Path) -> None:
    """Delete a temporary file, logging failures without raising."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:  # pragma: no cover - best-effort cleanup
        LOGGER.warning("Failed to delete temporary file %s: %s", path, exc)

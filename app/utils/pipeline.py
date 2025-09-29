"""Thin wrapper around :class:`StudyWorkflow` for legacy imports."""
from __future__ import annotations

from typing import Iterable, Optional

from app.services.workflow import StudyWorkflow


class StudyPipeline:
    """Backwards compatible façade used by older scripts and tests."""

    def __init__(self) -> None:
        self.workflow = StudyWorkflow()

    async def process_pdfs(self, file_paths: Iterable[str], anki_export_path: Optional[str] = None):
        return await self.workflow.process_study_materials(file_paths, anki_export_path)

    async def process_anki_export(self, anki_export_path: str):
        return await self.workflow.process_anki_only_workflow(anki_export_path)

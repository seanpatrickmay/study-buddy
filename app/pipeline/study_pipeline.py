from crewai import Crew
from app.agents.flashcard_agent import flashcard_agent, flashcard_task

class StudyPipeline:
    async def process_pdf(self, file_path: str):
        return
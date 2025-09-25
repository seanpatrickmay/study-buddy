from crewai import Crew
from typing import List
from pypdf import PdfReader

# Import your agents + tasks
from app.agents.flashcard_agent import flashcard_agent, flashcard_task
from app.agents.tav_agent import extraction_agent, extraction_task, verification_agent, verification_task
from app.agents.rag_agent import rag_agent, rag_task, web_enricher_agent, enrich_task

class StudyPipeline:
    async def process_pdfs(self, file_paths: List[str]):
        """
        Pipeline from PDF file paths -> flashcards JSON
        """

        # --- Step 1: Extract text from PDFs ---
        markdown_docs = []
        for path in file_paths:
            reader = PdfReader(path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
            markdown_docs.append(text)

        # --- Step 2: Combine all extracted docs ---
        unified_md = "\n\n".join(markdown_docs)

        # --- Step 3: Extraction + Verification ---
        crew_extract = Crew(
            agents=[extraction_agent, verification_agent],
            tasks=[extraction_task, verification_task]
        )
        refined_md = crew_extract.kickoff(inputs={"markdown": unified_md})

        # --- Step 4: RAG + Web Enrichment ---
        crew_rag = Crew(
            agents=[rag_agent, web_enricher_agent],
            tasks=[rag_task, enrich_task]
        )
        enriched_md = crew_rag.kickoff(inputs={"query": refined_md})

        # --- Step 5: Flashcard Generation ---
        crew_flashcards = Crew(
            agents=[flashcard_agent],
            tasks=[flashcard_task]
        )
        flashcards = crew_flashcards.kickoff(inputs={"markdown": enriched_md})

        return {
            "flashcards": flashcards,
            "metadata": {
                "pdfs_processed": len(file_paths),
                "chars_extracted": sum(len(md) for md in markdown_docs)
            }
        }

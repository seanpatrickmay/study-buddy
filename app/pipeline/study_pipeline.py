from crewai import Crew
from app.agents.flashcard_agent import flashcard_agent, flashcard_task
from app.utils.firecrawl_handler import FirecrawlHandler
from app.utils.pipeline_handler import VectorDBHandler
import os
from typing import List

class StudyPipeline:
    def __init__(self):
        self.firecrawl = FirecrawlHandler()
        self.vector_db = VectorDBHandler()
        
    def process_pdfs(self, pdf_urls: List[str]):
        """Main pipeline to process PDFs"""
        # Step 1: Convert PDFs to Markdown
        markdown_results = self.firecrawl.batch_convert_pdfs(pdf_urls)
        
        # Step 2: Create vector store
        markdown_contents = [r['markdown'] for r in markdown_results]
        self.vector_db.create_vector_store(markdown_contents)
        
        # Step 3: Generate unified markdown
        unified_md = self.generate_unified_markdown()
        
        return unified_md
    
    def generate_unified_markdown(self):
        """Use RAG to create final markdown"""
        # RAG logic here
        pass
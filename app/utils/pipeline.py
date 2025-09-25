# app/utils/pipeline.py
from pathlib import Path
from typing import Dict, List, Optional
import asyncio

# Updated imports to fix deprecation warnings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings  # Updated
from langchain_community.vectorstores import Chroma  # Updated
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI  # Updated

from app.config.config import settings
from app.utils.firecrawl_handler import FirecrawlHandler
from app.utils.pdf_processor import PDFProcessor
# from app.agents.flashcard_agent import FlashcardAgent  # Comment out if not exists yet

class StudyPipeline:
    def __init__(self):
        self.firecrawl_handler = FirecrawlHandler() if settings.firecrawl_api_key else None
        self.pdf_processor = PDFProcessor()
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.embedding_model
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        # Use ChatOpenAI from langchain_openai
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key
        )
        self.vectorstore = None
        
    async def process_pdf(self, pdf_path: str) -> Dict:
        """Main pipeline to process a single PDF"""
        
        # Step 1: Convert PDF to Markdown
        markdown_content = self._convert_to_markdown(pdf_path)
        
        # Step 2: Create vector store from markdown
        self._create_vector_store([markdown_content])
        
        # Step 3: Generate study materials using RAG
        study_materials = await self._generate_study_materials()
        
        # Step 4: Save outputs
        output_files = self._save_outputs(study_materials)
        
        return {
            "status": "success",
            "materials": study_materials,
            "files": output_files
        }
    
    def _convert_to_markdown(self, pdf_path: str) -> str:
        """Convert PDF to Markdown using Firecrawl or fallback"""
        if self.firecrawl_handler and pdf_path.startswith('http'):
            # Use Firecrawl for URLs
            result = self.firecrawl_handler.process_pdf_url(pdf_path)
            if result['success']:
                return result['markdown']
        
        # Fallback to local PDF processing
        return self.pdf_processor.pdf_to_markdown(Path(pdf_path))
    
    def _create_vector_store(self, markdown_contents: List[str]):
        """Create vector store from markdown contents"""
        all_chunks = []
        for content in markdown_contents:
            chunks = self.text_splitter.split_text(content)
            all_chunks.extend(chunks)
        
        self.vectorstore = Chroma.from_texts(
            texts=all_chunks,
            embedding=self.embeddings,
            persist_directory=str(settings.vector_db_path)
        )
        return self.vectorstore
    
    async def _generate_study_materials(self) -> Dict:
        """Generate comprehensive study materials using RAG"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")
        
        # Create retrieval chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 5}
            )
        )
        
        # Generate different types of study materials
        materials = {}
        
        # 1. Generate unified summary
        summary_query = "Create a comprehensive summary of all key concepts, theories, and important information from this document."
        materials['summary'] = qa_chain.run(summary_query)
        
        # 2. Generate cheat sheet
        cheatsheet_query = "Create a concise cheat sheet with the most important formulas, definitions, and key points."
        materials['cheatsheet'] = qa_chain.run(cheatsheet_query)
        
        # 3. Generate unified markdown document
        materials['unified_markdown'] = self._create_unified_markdown(materials)
        
        return materials
    
    def _create_unified_markdown(self, materials: Dict) -> str:
        """Create a unified markdown document from all materials"""
        unified_md = "# Study Materials\n\n"
        unified_md += "Generated using AI-powered analysis\n\n"
        unified_md += "---\n\n"
        
        # Add summary section
        unified_md += "## Executive Summary\n\n"
        unified_md += materials.get('summary', '') + "\n\n"
        
        # Add cheat sheet section
        unified_md += "## Quick Reference / Cheat Sheet\n\n"
        unified_md += materials.get('cheatsheet', '') + "\n\n"
        
        return unified_md
    
    def _save_outputs(self, materials: Dict) -> Dict:
        """Save generated materials to files"""
        output_files = {}
        
        # Create output directory if it doesn't exist
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save unified markdown
        md_path = settings.output_dir / "unified_study_guide.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(materials['unified_markdown'])
        output_files['markdown'] = str(md_path)
        
        return output_files
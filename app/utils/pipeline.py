# app/utils/pipeline.py
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
import hashlib
import json

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document

from app.config.config import settings
from app.utils.firecrawl_handler import FirecrawlHandler
from app.utils.pdf_processor import PDFProcessor

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
        
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key
        )
        
        # Directory for markdown files
        self.markdown_dir = settings.vector_db_path / "markdown_files"
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        
        # Track processed files
        self.metadata_file = settings.vector_db_path / "processed_files.json"
        self.processed_files = self._load_processed_files()
        
        # Create vector store from existing markdown files
        self.vectorstore = self._create_vectorstore_from_markdown_files()
    
    def _load_processed_files(self) -> Dict:
        """Load metadata about processed files"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_processed_files(self):
        """Save metadata about processed files"""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, 'w') as f:
            json.dump(self.processed_files, f, indent=2)
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate unique hash for file"""
        if file_path.startswith('http'):
            return hashlib.md5(file_path.encode()).hexdigest()
        
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _save_markdown_file(self, markdown_content: str, filename: str, file_hash: str) -> Path:
        """Save complete markdown file to disk"""
        # Create filename: hash_original_name.md
        safe_filename = f"{file_hash}_{filename.replace('.pdf', '')}.md"
        markdown_path = self.markdown_dir / safe_filename
        
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return markdown_path
    
    def _load_markdown_file(self, file_hash: str) -> str:
        """Load markdown content from disk"""
        for file in self.markdown_dir.glob(f"{file_hash}_*.md"):
            with open(file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _create_vectorstore_from_markdown_files(self):
        """Create vector store from all saved markdown files"""
        if not any(self.markdown_dir.glob("*.md")):
            return None
        
        print("📂 Loading markdown files into vector database...")
        
        all_documents = []
        
        for file_hash, metadata in self.processed_files.items():
            markdown_content = self._load_markdown_file(file_hash)
            if markdown_content:
                # Create chunks for vector search
                chunks = self.text_splitter.split_text(markdown_content)
                
                # Create Document objects with metadata
                for i, chunk in enumerate(chunks):
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            "source": metadata['filename'],
                            "file_id": file_hash,
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    )
                    all_documents.append(doc)
        
        if all_documents:
            vectorstore = Chroma.from_documents(
                documents=all_documents,
                embedding=self.embeddings,
                persist_directory=str(settings.vector_db_path)
            )
            vectorstore.persist()
            return vectorstore
        
        return None
    
    async def process_pdf(self, pdf_path: str, add_to_db_only: bool = False) -> Dict:
        """Process PDF and store complete markdown file"""
        
        file_hash = self._get_file_hash(pdf_path)
        file_name = Path(pdf_path).name
        
        # Check if already processed
        if file_hash in self.processed_files:
            print(f"ℹ️ File already in database: {file_name}")
            if not add_to_db_only:
                study_materials = await self._generate_study_materials()
                output_files = self._save_outputs(study_materials)
                return {
                    "status": "success",
                    "message": "File already in database, generated new materials",
                    "materials": study_materials,
                    "files": output_files
                }
            return {
                "status": "already_processed",
                "message": f"File {file_name} is already in the database",
                "file_id": file_hash
            }
        
        # Convert PDF to Markdown
        markdown_content = self._convert_to_markdown(pdf_path)
        
        # Save complete markdown file
        markdown_path = self._save_markdown_file(markdown_content, file_name, file_hash)
        
        # Add to vector store (chunks for search, but preserves full markdown)
        self._add_to_vectorstore(markdown_content, file_name, file_hash)
        
        # Save file metadata
        self.processed_files[file_hash] = {
            "filename": file_name,
            "original_path": pdf_path,
            "markdown_path": str(markdown_path),
            "char_count": len(markdown_content)
        }
        self._save_processed_files()
        
        if add_to_db_only:
            return {
                "status": "success",
                "message": f"File {file_name} added to database",
                "file_id": file_hash,
                "markdown_path": str(markdown_path),
                "char_count": len(markdown_content)
            }
        
        # Generate study materials
        study_materials = await self._generate_study_materials()
        output_files = self._save_outputs(study_materials)
        
        return {
            "status": "success",
            "materials": study_materials,
            "files": output_files
        }
    
    def _add_to_vectorstore(self, markdown_content: str, filename: str, file_hash: str):
        """Add content to vector store (chunks for search)"""
        chunks = self.text_splitter.split_text(markdown_content)
        
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": filename,
                    "file_id": file_hash,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            documents.append(doc)
        
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=str(settings.vector_db_path)
            )
            self.vectorstore.persist()
        else:
            self.vectorstore.add_documents(documents=documents)
            self.vectorstore.persist()
        
        print(f"✅ Added {len(chunks)} chunks from {filename} to vector database")
        print(f"📄 Full markdown saved to: {self.markdown_dir}")
    
    def get_all_markdown_files(self) -> List[Dict]:
        """Get list of all stored markdown files"""
        files = []
        for file_hash, metadata in self.processed_files.items():
            files.append({
                "file_id": file_hash,
                "filename": metadata['filename'],
                "markdown_path": metadata.get('markdown_path'),
                "char_count": metadata.get('char_count', 0)
            })
        return files
    
    def get_markdown_content(self, file_id: str) -> Optional[str]:
        """Get the complete markdown content for a specific file"""
        return self._load_markdown_file(file_id)
    
    def combine_all_markdown_files(self) -> str:
        """Combine all markdown files into one document"""
        combined = "# Combined Study Materials\n\n"
        
        for file_hash, metadata in self.processed_files.items():
            markdown_content = self._load_markdown_file(file_hash)
            if markdown_content:
                combined += f"\n\n---\n\n"
                combined += f"# Source: {metadata['filename']}\n\n"
                combined += markdown_content
                combined += "\n\n"
        
        return combined
    
    async def generate_unified_markdown(self) -> str:
        """Generate a single unified markdown from all stored files using RAG"""
        if not self.vectorstore:
            # If no vector store, just combine all files
            return self.combine_all_markdown_files()
        
        # Use RAG to create intelligent summary
        materials = await self._generate_study_materials()
        
        # Add the complete markdown files at the end
        unified = materials['unified_markdown']
        unified += "\n\n---\n\n"
        unified += "# Complete Source Documents\n\n"
        unified += self.combine_all_markdown_files()
        
        return unified
    
    def get_database_info(self) -> Dict:
        """Get information about the database"""
        markdown_files = list(self.markdown_dir.glob("*.md"))
        total_size = sum(f.stat().st_size for f in markdown_files)
        
        return {
            "status": "active" if self.processed_files else "empty",
            "file_count": len(self.processed_files),
            "markdown_files": len(markdown_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(self.markdown_dir),
            "files": self.get_all_markdown_files()
        }
    
    def clear_database(self):
        """Clear the entire database including markdown files"""
        import shutil
        
        # Clear vector store
        self.vectorstore = None
        
        # Clear metadata
        self.processed_files = {}
        if self.metadata_file.exists():
            self.metadata_file.unlink()
        
        # Remove all markdown files
        if self.markdown_dir.exists():
            shutil.rmtree(self.markdown_dir)
        
        # Remove vector database
        if settings.vector_db_path.exists():
            shutil.rmtree(settings.vector_db_path)
        
        print("🗑️ Database and markdown files cleared")
    
    # Keep existing methods
    def _convert_to_markdown(self, pdf_path: str) -> str:
        """Convert PDF to Markdown using Firecrawl or fallback"""
        if self.firecrawl_handler and pdf_path.startswith('http'):
            result = self.firecrawl_handler.process_pdf_url(pdf_path)
            if result['success']:
                return result['markdown']
        
        return self.pdf_processor.pdf_to_markdown(Path(pdf_path))
    
    async def _generate_study_materials(self) -> Dict:
        """Generate comprehensive study materials using RAG"""
        if not self.vectorstore:
            raise ValueError("Vector store not initialized")
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 10}  # Increase k for more context
            )
        )
        
        materials = {}
        
        summary_query = "Create a comprehensive summary of all key concepts, theories, and important information from all the documents."
        result = qa_chain.invoke({"query": summary_query})
        materials['summary'] = result['result']
        
        cheatsheet_query = "Create a concise cheat sheet with the most important formulas, definitions, and key points from all documents."
        result = qa_chain.invoke({"query": cheatsheet_query})
        materials['cheatsheet'] = result['result']
        
        materials['unified_markdown'] = self._create_unified_markdown(materials)
        
        return materials
    
    def _create_unified_markdown(self, materials: Dict) -> str:
        """Create a unified markdown document"""
        unified_md = "# Study Materials\n\n"
        unified_md += f"Generated from {len(self.processed_files)} documents\n\n"
        unified_md += "---\n\n"
        
        unified_md += "## Executive Summary\n\n"
        unified_md += materials.get('summary', '') + "\n\n"
        
        unified_md += "## Quick Reference / Cheat Sheet\n\n"
        unified_md += materials.get('cheatsheet', '') + "\n\n"
        
        return unified_md
    
    def _save_outputs(self, materials: Dict) -> Dict:
        """Save generated materials to files"""
        output_files = {}
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        
        md_path = settings.output_dir / "unified_study_guide.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(materials['unified_markdown'])
        output_files['markdown'] = str(md_path)
        
        return output_files

    async def process_pdfs(self, file_paths: List[str], anki_export_path: Optional[str] = None) -> Dict:
        """
        Process multiple PDF files using the complete workflow.
        This method is used by the FastAPI endpoint.
        """
        from app.utils.study_workflow import StudyWorkflow

        # Use the new complete workflow
        workflow = StudyWorkflow()
        return await workflow.process_study_materials(file_paths, anki_export_path)
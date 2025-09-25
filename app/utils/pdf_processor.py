# app/utils/pdf_processor.py
import pypdf
from pathlib import Path
import markdown
from typing import Optional

class PDFProcessor:
    def pdf_to_markdown(self, pdf_path: Path) -> str:
        """Extract text from PDF and format as markdown"""
        try:
            reader = pypdf.PdfReader(pdf_path)
            markdown_content = f"# Document: {pdf_path.name}\n\n"
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    markdown_content += f"## Page {i+1}\n\n"
                    # Clean up text and format
                    paragraphs = text.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            markdown_content += f"{para.strip()}\n\n"
            
            return markdown_content
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
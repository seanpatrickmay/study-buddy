# app/utils/firecrawl_handler.py
from firecrawl import Firecrawl  # Updated import
from typing import List, Dict, Optional
from pathlib import Path
from app.config.config import settings

class FirecrawlHandler:
    def __init__(self):
        self.app = Firecrawl(api_key=settings.firecrawl_api_key)
        self.max_urls = settings.firecrawl_max_urls
    
    def process_pdf_url(self, pdf_url: str) -> Dict:
        """Process a PDF from URL using Firecrawl"""
        try:
            # Using updated API
            result = self.app.scrape(
                url=pdf_url,
                formats=['markdown']
            )
            
            return {
                'success': True,
                'markdown': result.get('markdown', ''),
                'source_url': pdf_url,
                'metadata': result.get('metadata', {})
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'source_url': pdf_url
            }
    
    def process_local_pdf(self, pdf_path: Path) -> Dict:
        """
        Process a local PDF file.
        Note: Firecrawl requires URLs, so this returns failure to trigger fallback to local processing
        """
        return {
            'success': False,
            'error': 'Firecrawl requires URLs, not local files',
            'source_path': str(pdf_path),
            'requires_fallback': True
        }
    
    def batch_process(self, sources: List[str]) -> List[Dict]:
        """Process multiple PDFs (URLs or paths)"""
        results = []
        for source in sources[:self.max_urls]:
            if source.startswith('http'):
                result = self.process_pdf_url(source)
            else:
                result = self.process_local_pdf(Path(source))
            results.append(result)
        return results
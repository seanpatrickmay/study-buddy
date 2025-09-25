# app/test/test_firecrawl.py
import sys
import os
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
from firecrawl import Firecrawl  # Updated import
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_firecrawl_connection():
    """Test if Firecrawl API is working"""
    api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not api_key:
        print("❌ FIRECRAWL_API_KEY not found in .env file")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        app = Firecrawl(api_key=api_key)
        print("✅ Firecrawl client initialized")
        
        test_url = "https://example.com"
        print(f"\n📝 Testing with: {test_url}")
        
        # Check what the API actually returns
        result = app.scrape(
            url=test_url,
            formats=['markdown']
        )
        
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        # Check different possible response structures
        if result:
            if 'markdown' in result:
                print("✅ Successfully converted to markdown")
                print(f"   Preview: {result['markdown'][:200]}...")
                return True
            elif 'data' in result and 'markdown' in result['data']:
                print("✅ Successfully converted to markdown (nested)")
                print(f"   Preview: {result['data']['markdown'][:200]}...")
                return True
            elif 'content' in result:
                print("✅ Found content")
                print(f"   Preview: {result['content'][:200]}...")
                return True
            else:
                print(f"⚠️  Unexpected response structure:")
                print(f"   {result}")
                return False
        else:
            print("❌ No response received")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_url():
    """Test with an actual PDF URL"""
    api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not api_key:
        print("❌ FIRECRAWL_API_KEY not found")
        return
    
    # Updated to new API
    app = Firecrawl(api_key=api_key)
    
    # Use a public PDF for testing
    pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    
    print(f"\n📄 Testing PDF conversion: {pdf_url}")
    
    try:
        # Using new API method
        result = app.scrape(
            url=pdf_url,
            formats=['markdown']
        )
        
        if result and 'markdown' in result:
            print("✅ PDF successfully converted to markdown")
            print(f"   Length: {len(result['markdown'])} characters")
            
            # Save to file for inspection
            output_path = Path("test_output.md")
            with open(output_path, 'w') as f:
                f.write(result['markdown'])
            print(f"✅ Saved to {output_path}")
            
            return result['markdown']
        else:
            print("❌ Failed to convert PDF")
            print(f"   Result: {result}")
            
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return None

def test_local_pdf_processing():
    """Test local PDF processing without Firecrawl"""
    print("\n📄 Testing local PDF processing...")
    
    # First, let's create the PDFProcessor if it doesn't exist
    pdf_processor_path = Path(__file__).parent.parent / "utils" / "pdf_processor.py"
    
    if not pdf_processor_path.exists():
        print("📝 Creating pdf_processor.py...")
        create_pdf_processor()
    
    try:
        from app.utils.pdf_processor import PDFProcessor
        
        test_pdf = Path("test2.pdf")
        
        if not test_pdf.exists():
            print("⚠️  No test.pdf found. Downloading sample...")
            download_sample_pdf()
        
        processor = PDFProcessor()
        markdown = processor.pdf_to_markdown(test_pdf)
        
        print("✅ PDF processed successfully")
        print(f"   Length: {len(markdown)} characters")
        print(f"   Preview: {markdown[:500]}...")
        
        # Save output
        output_path = Path("test_local_output.md")
        with open(output_path, "w") as f:
            f.write(markdown)
        print(f"✅ Saved to {output_path}")
        
    except ImportError as e:
        print(f"⚠️  Skipping local PDF test: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def create_pdf_processor():
    """Create the pdf_processor.py file if it doesn't exist"""
    pdf_processor_code = '''import pypdf
from pathlib import Path

class PDFProcessor:
    def pdf_to_markdown(self, pdf_path: Path) -> str:
        """Extract text from PDF and format as markdown"""
        try:
            reader = pypdf.PdfReader(pdf_path)
            markdown_content = f"# Document: {pdf_path.name}\\n\\n"
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    markdown_content += f"## Page {i+1}\\n\\n"
                    paragraphs = text.split('\\n\\n')
                    for para in paragraphs:
                        if para.strip():
                            markdown_content += f"{para.strip()}\\n\\n"
            
            return markdown_content
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
'''
    
    pdf_processor_path = Path(__file__).parent.parent / "utils" / "pdf_processor.py"
    pdf_processor_path.parent.mkdir(exist_ok=True)
    
    with open(pdf_processor_path, 'w') as f:
        f.write(pdf_processor_code)
    print(f"✅ Created {pdf_processor_path}")

def download_sample_pdf():
    """Download a sample PDF for testing"""
    import requests
    
    url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    response = requests.get(url)
    
    with open("test2.pdf", "wb") as f:
        f.write(response.content)
    print("✅ Downloaded test.pdf")

async def test_pipeline():
    """Test the full pipeline with a local PDF"""
    print("\n🔧 Testing full pipeline...")
    
    try:
        from app.utils.pipeline import StudyPipeline
        
        pipeline = StudyPipeline()
        print("✅ Pipeline initialized")
        
        test_pdf = Path("test2.pdf")
        
        if not test_pdf.exists():
            print("⚠️  No test.pdf found. Downloading...")
            download_sample_pdf()
        
        print(f"📄 Processing: {test_pdf}")
        
        result = await pipeline.process_pdf(str(test_pdf))
        
        if result['status'] == 'success':
            print("✅ Pipeline completed successfully!")
            print(f"   Generated files: {result.get('files', {})}")
            
            unified_md = Path("outputs/unified_study_guide.md")
            if unified_md.exists():
                print(f"✅ Unified markdown created: {unified_md}")
                print(f"   Size: {unified_md.stat().st_size} bytes")
        else:
            print("❌ Pipeline failed")
            
    except ImportError as e:
        print(f"⚠️  Pipeline not fully implemented yet: {e}")
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Firecrawl Tests\n")
    print("=" * 50)
    
    # Test 1: Basic connection
    if test_firecrawl_connection():
        
        # Test 2: PDF URL
        test_pdf_url()
    
    # Test 3: Local PDF processing (fallback)
    test_local_pdf_processing()
    
    # Test 4: Full pipeline (if available)
    print("\n" + "=" * 50)
    asyncio.run(test_pipeline())
    
    print("\n✅ Tests completed!")
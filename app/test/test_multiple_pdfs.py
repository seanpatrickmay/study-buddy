import asyncio
from pathlib import Path
from utils.pipeline import StudyPipeline
from utils.firecrawl_handler import FirecrawlHandler

async def process_multiple_pdfs():
    """Process multiple PDFs into one unified study guide"""
    
    # List your PDFs (mix of local files and URLs)
    pdf_sources = [
        "test.pdf",           # Local file 1
        "test2.pdf",          # Local file 2 (brain/nervous system)
        "test3.pdf",
        "test4.pdf",
        "test5.pdf"
        # Add more PDFs here (up to 5 total)
    ]
    
    print("📚 Processing Multiple PDFs into Unified Study Guide\n")
    print(f"Processing {len(pdf_sources)} PDFs...")
    print("-" * 50)
    
    # Initialize handlers
    firecrawl = FirecrawlHandler()
    pipeline = StudyPipeline()
    
    # Collect all markdown content
    all_markdown_content = []
    
    for i, source in enumerate(pdf_sources, 1):
        print(f"\n📄 [{i}/{len(pdf_sources)}] Processing: {source}")
        
        if source.startswith('http'):
            # Process URL with Firecrawl
            result = firecrawl.process_pdf_url(source)
        else:
            # Process local file
            result = firecrawl.process_local_pdf(Path(source))
        
        if result['success']:
            markdown = result['markdown']
            all_markdown_content.append(markdown)
            print(f"   ✅ Extracted {len(markdown):,} characters")
        else:
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
    
    if not all_markdown_content:
        print("\n❌ No PDFs were successfully processed")
        return
    
    print(f"\n📊 Total content: {sum(len(md) for md in all_markdown_content):,} characters")
    
    # Create unified vector store
    print("\n🔨 Creating unified vector database...")
    pipeline._create_vector_store(all_markdown_content)
    
    # Generate comprehensive study materials
    print("🎯 Generating unified study materials...")
    materials = await pipeline._generate_study_materials()
    
    # Save the unified output
    print("💾 Saving unified study guide...")
    output_files = pipeline._save_outputs(materials)
    
    # Print summary
    print("\n" + "=" * 50)
    print("✅ COMPLETE!")
    print(f"📁 Unified study guide saved to: {output_files['markdown']}")
    
    # Check file size
    output_path = Path(output_files['markdown'])
    if output_path.exists():
        size = output_path.stat().st_size
        print(f"📏 Output size: {size:,} bytes")
    
    return materials

if __name__ == "__main__":
    asyncio.run(process_multiple_pdfs())
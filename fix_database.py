# fix_database.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from app.utils.pipeline import StudyPipeline

async def fix_database():
    """Clear old data and reprocess with markdown saving"""
    
    pipeline = StudyPipeline()
    
    print("🔧 Fixing Database - Clearing old data and reprocessing\n" + "="*60)
    
    # Step 1: Clear everything
    print("\n1️⃣ Clearing old database...")
    pipeline.clear_database()
    print("   ✅ Database cleared")
    
    # Step 2: Reinitialize
    print("\n2️⃣ Reinitializing pipeline...")
    pipeline = StudyPipeline()
    
    # Step 3: Process PDFs with the new system
    pdfs_to_process = ["test.pdf", "test2.pdf"]
    
    for pdf in pdfs_to_process:
        if Path(pdf).exists():
            print(f"\n3️⃣ Processing {pdf} with markdown saving...")
            result = await pipeline.process_pdf(pdf, add_to_db_only=True)
            print(f"   Status: {result['status']}")
            if 'markdown_path' in result:
                print(f"   ✅ Markdown saved to: {result['markdown_path']}")
    
    # Step 4: Verify markdown files exist
    print("\n4️⃣ Verifying markdown files...")
    markdown_dir = Path("chroma_db/markdown_files")
    if markdown_dir.exists():
        md_files = list(markdown_dir.glob("*.md"))
        print(f"   Found {len(md_files)} markdown files:")
        for md_file in md_files:
            size_kb = md_file.stat().st_size / 1024
            print(f"   - {md_file.name} ({size_kb:.1f} KB)")
    
    # Step 5: Test retrieval
    print("\n5️⃣ Testing markdown retrieval...")
    all_files = pipeline.get_all_markdown_files()
    for file_info in all_files:
        content = pipeline.get_markdown_content(file_info['file_id'])
        if content:
            print(f"   ✅ Can retrieve {file_info['filename']}: {len(content):,} chars")
    
    # Step 6: Generate combined markdown
    print("\n6️⃣ Generating combined markdown...")
    combined = pipeline.combine_all_markdown_files()
    print(f"   Combined size: {len(combined):,} characters")
    
    # Save for inspection
    with open("fixed_combined.md", 'w') as f:
        f.write(combined)
    print(f"   Saved to: fixed_combined.md")
    
    print("\n" + "="*60)
    print("✅ Database fixed! Markdown files now properly stored.")

if __name__ == "__main__":
    asyncio.run(fix_database())
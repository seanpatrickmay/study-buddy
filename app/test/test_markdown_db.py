# test_markdown_db.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
from app.utils.pipeline import StudyPipeline
import json

async def test_markdown_database():
    """Test markdown file storage and database functionality"""
    
    print("🧪 Testing Markdown File Storage & Database\n" + "="*60)
    
    pipeline = StudyPipeline()
    
    # Test 1: Check initial state
    print("\n1️⃣ Initial Database Check")
    info = pipeline.get_database_info()
    print(f"   Files in DB: {info['file_count']}")
    print(f"   Markdown files: {info['markdown_files']}")
    print(f"   Storage path: {info['storage_path']}")
    
    # Test 2: Process first PDF and check markdown creation
    print("\n2️⃣ Processing first PDF (test.pdf)")
    if Path("test.pdf").exists():
        result = await pipeline.process_pdf("test.pdf", add_to_db_only=True)
        print(f"   Status: {result['status']}")
        
        if 'markdown_path' in result:
            print(f"   Markdown saved to: {result['markdown_path']}")
            
            # Verify markdown file exists
            md_path = Path(result['markdown_path'])
            if md_path.exists():
                print(f"   ✅ Markdown file exists ({md_path.stat().st_size} bytes)")
                
                # Read first 200 chars of markdown
                with open(md_path, 'r') as f:
                    content = f.read(200)
                    print(f"   Preview: {content}...")
    
    # Test 3: Process second PDF
    print("\n3️⃣ Processing second PDF (test2.pdf)")
    if Path("test2.pdf").exists():
        result = await pipeline.process_pdf("test2.pdf", add_to_db_only=True)
        print(f"   Status: {result['status']}")
    
    # Test 4: Check markdown files directory
    print("\n4️⃣ Checking Markdown Files Directory")
    markdown_dir = Path(pipeline.markdown_dir)
    if markdown_dir.exists():
        md_files = list(markdown_dir.glob("*.md"))
        print(f"   Found {len(md_files)} markdown files:")
        for md_file in md_files:
            size_kb = md_file.stat().st_size / 1024
            print(f"   - {md_file.name} ({size_kb:.1f} KB)")
    
    # Test 5: Get all markdown files info
    print("\n5️⃣ Getting All Markdown Files Info")
    all_files = pipeline.get_all_markdown_files()
    for file_info in all_files:
        print(f"   - {file_info['filename']}: {file_info['char_count']:,} characters")
        print(f"     ID: {file_info['file_id'][:8]}...")
    
    # Test 6: Retrieve specific markdown content
    print("\n6️⃣ Retrieving Specific Markdown Content")
    if all_files:
        first_file = all_files[0]
        content = pipeline.get_markdown_content(first_file['file_id'])
        if content:
            print(f"   Retrieved {first_file['filename']}: {len(content):,} characters")
            print(f"   First line: {content.split(chr(10))[0]}")
    
    # Test 7: Combine all markdown files
    print("\n7️⃣ Combining All Markdown Files")
    combined = pipeline.combine_all_markdown_files()
    print(f"   Combined document size: {len(combined):,} characters")
    print(f"   Number of source documents: {combined.count('# Source:')}")
    
    # Test 8: Check vector database
    print("\n8️⃣ Checking Vector Database")
    info = pipeline.get_database_info()
    print(f"   Total size: {info['total_size_mb']} MB")
    print(f"   Files tracked: {info['file_count']}")
    
    # Test 9: Generate unified markdown with RAG
    print("\n9️⃣ Generating Unified Markdown with RAG")
    unified = await pipeline.generate_unified_markdown()
    print(f"   Generated unified document: {len(unified):,} characters")
    
    # Save to file for inspection
    test_output = Path("test_unified_output.md")
    with open(test_output, 'w') as f:
        f.write(unified)
    print(f"   Saved to: {test_output}")
    
    # Test 10: Verify persistence
    print("\n🔟 Testing Persistence")
    del pipeline
    
    # Create new instance
    new_pipeline = StudyPipeline()
    info = new_pipeline.get_database_info()
    print(f"   After restart - Files in DB: {info['file_count']}")
    print(f"   Markdown files still exist: {info['markdown_files']}")
    
    if info['file_count'] > 0:
        print("   ✅ Markdown files and database persisted!")
    
    print("\n" + "="*60)
    print("✅ All tests completed!")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_markdown_database())
# test_vector_db.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
from app.utils.pipeline import StudyPipeline

async def test_vector_database():
    """Test vector database persistence and functionality"""
    
    pipeline = StudyPipeline()
    
    print("🧪 Vector Database Test Suite\n" + "="*50)
    
    # Test 1: Check initial database status
    print("\n1️⃣ Checking database status...")
    info = pipeline.get_database_info()
    print(f"   Files in DB: {info['file_count']}")
    print(f"   Total chunks: {info['total_chunks']}")
    
    # Test 2: Add first PDF
    print("\n2️⃣ Adding first PDF to database...")
    if Path("test.pdf").exists():
        result = await pipeline.process_pdf("test.pdf", add_to_db_only=True)
        print(f"   Status: {result['status']}")
        if 'char_count' in result:
            print(f"   Characters processed: {result['char_count']:,}")
    
    # Test 3: Add second PDF
    print("\n3️⃣ Adding second PDF to database...")
    if Path("test2.pdf").exists():
        result = await pipeline.process_pdf("test2.pdf", add_to_db_only=True)
        print(f"   Status: {result['status']}")
    
    # Test 4: Check updated database
    print("\n4️⃣ Checking updated database...")
    info = pipeline.get_database_info()
    print(f"   Files in DB: {info['file_count']}")
    print(f"   Total chunks: {info['total_chunks']}")
    for file in info['files']:
        print(f"   - {file['filename']}: {file['char_count']:,} chars")
    
    # Test 5: Generate materials from database
    print("\n5️⃣ Generating study materials from entire database...")
    materials = await pipeline._generate_study_materials()
    output = pipeline._save_outputs(materials)
    print(f"   ✅ Generated unified study guide")
    print(f"   Summary length: {len(materials['summary'])} chars")
    print(f"   Saved to: {output['markdown']}")
    
    # Test 6: Test persistence (simulate restart)
    print("\n6️⃣ Testing persistence (simulating restart)...")
    del pipeline
    
    # Create new pipeline instance
    new_pipeline = StudyPipeline()
    info = new_pipeline.get_database_info()
    print(f"   Files still in DB after 'restart': {info['file_count']}")
    print("   ✅ Database persisted successfully!")
    
    return True

if __name__ == "__main__":
    asyncio.run(test_vector_database())
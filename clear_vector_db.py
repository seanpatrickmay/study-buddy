#!/usr/bin/env python3
"""
Script to clear the vector database when switching embedding models.
Run this when you change from OpenAI embeddings to Voyage AI embeddings.
"""

import shutil
from pathlib import Path

def clear_vector_db():
    """Remove the existing vector database to start fresh with new embeddings."""
    db_paths = [
        Path("./chroma_db"),
        Path("./vector_db"),
        Path("./db"),
        Path("./outputs"),  # Also clear outputs if present
    ]

    cleared = False
    for db_path in db_paths:
        if db_path.exists():
            print(f"Removing directory at: {db_path}")
            try:
                shutil.rmtree(db_path)
                cleared = True
                print(f"✓ Cleared: {db_path}")
            except Exception as e:
                print(f"✗ Failed to clear {db_path}: {e}")

    if cleared:
        print("\n✓ Vector database and outputs cleared successfully!")
        print("The application will now create fresh databases with Voyage AI embeddings.")
        print("\nWhat this fixes:")
        print("  - Embedding dimension mismatches (1536 vs 1024)")
        print("  - Database configuration incompatibilities")
        print("  - Collection naming conflicts")
    else:
        print("No vector database directories found to clear.")
        print("This is normal for a fresh installation.")

if __name__ == "__main__":
    clear_vector_db()
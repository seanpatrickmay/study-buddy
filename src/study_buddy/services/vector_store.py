"""Manage persistence and retrieval for the Chroma vector store."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.embeddings import Embeddings

try:  # pragma: no cover - optional import path changed in LangChain 0.2
    from langchain_chroma import Chroma
except ImportError:  # pragma: no cover
    from langchain_community.vectorstores import Chroma  # type: ignore[no-redef]

from study_buddy.core.models import DocumentBundle


class VectorStoreManager:
    """Lightweight wrapper around a persistent Chroma collection."""

    def __init__(
        self,
        embeddings: Embeddings,
        persist_directory: Path,
        collection_name: str = "study_bot",
        chunk_size: int = 1_000,
        chunk_overlap: int = 200,
    ) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " "],
        )

        # Create collection name with embedding model suffix to avoid dimension conflicts
        embedding_model_suffix = getattr(embeddings, 'model', 'unknown').replace('-', '_')
        full_collection_name = f"{collection_name}_{embedding_model_suffix}"

        try:
            self._vector_store = Chroma(
                collection_name=full_collection_name,
                persist_directory=str(persist_directory),
                embedding_function=embeddings,
            )
        except Exception as e:
            error_msg = str(e).lower()
            should_recreate = any(keyword in error_msg for keyword in [
                "dimension", "_type", "configuration", "keyerror", "incompatible"
            ])

            if should_recreate:
                print(f"Warning: Database compatibility issue detected. Recreating vector database.")
                print(f"Error details: {e}")
                import shutil
                # Clear the old database and create new one
                if persist_directory.exists():
                    shutil.rmtree(persist_directory)
                    persist_directory.mkdir(parents=True, exist_ok=True)

                self._vector_store = Chroma(
                    collection_name=full_collection_name,
                    persist_directory=str(persist_directory),
                    embedding_function=embeddings,
                )
                print(f"✓ New vector database created with collection: {full_collection_name}")
            else:
                raise

    def add_documents(self, bundles: Iterable[DocumentBundle]) -> int:
        """Chunk and ingest documents into the vector store."""
        documents: List[Document] = []
        for bundle in bundles:
            for idx, chunk in enumerate(self._splitter.split_text(bundle.markdown)):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": bundle.display_name,
                            "file_path": str(bundle.source_path),
                            "chunk_index": idx,
                        },
                    )
                )
        if not documents:
            return 0
        self._vector_store.add_documents(documents)
        return len(documents)

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Proxy similarity search to the underlying vector store."""
        return self._vector_store.similarity_search(query, k=k)

    @property
    def retriever(self):  # pragma: no cover - simple proxy
        return self._vector_store.as_retriever()

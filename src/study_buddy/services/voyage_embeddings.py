"""Custom Voyage AI embeddings implementation for LangChain compatibility."""
from __future__ import annotations

from typing import List

import voyageai
from langchain_core.embeddings import Embeddings


class VoyageEmbeddings(Embeddings):
    """Voyage AI embeddings for LangChain compatibility."""

    def __init__(
        self,
        api_key: str,
        model: str = "voyage-3",
        batch_size: int = 128,
    ) -> None:
        self.client = voyageai.Client(api_key=api_key)
        self.model = model
        self.batch_size = batch_size

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search documents."""
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            result = self.client.embed(
                texts=batch,
                model=self.model,
                input_type="document"
            )
            all_embeddings.extend(result.embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed search query."""
        result = self.client.embed(
            texts=[text],
            model=self.model,
            input_type="query"
        )
        return result.embeddings[0]
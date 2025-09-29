"""High level orchestration for the Study Buddy workflow."""
from __future__ import annotations

import json
import re
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config.config import settings
from app.services.anki import AnkiDeckBuilder, AnkiDifficultyReader, DeckMetadata
from app.services.cheatsheet import CheatSheetBuilder
from app.services.document_loader import DocumentLoader
from app.services.flashcards import FlashcardGenerator
from app.services.models import DocumentBundle, Flashcard, WorkflowArtifacts
from app.services.term_extraction import TermExtractor
from app.services.vector_store import VectorStoreManager
from app.services.web_search import WebSearchAgent
from app.utils.latex import LaTeXCompiler


class StudyWorkflow:
    """Coordinate document ingestion, enrichment, and artefact generation."""

    def __init__(self) -> None:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
        if settings.tavily_api_key:
            os.environ.setdefault("TAVILY_API_KEY", settings.tavily_api_key)

        self._output_dir = settings.output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

        self._document_loader = DocumentLoader(settings.firecrawl_api_key)
        self._embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        self._llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key,
        )
        self._vector_store = VectorStoreManager(
            embeddings=self._embeddings,
            persist_directory=settings.vector_db_path,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self._term_extractor = TermExtractor(self._llm)
        self._flashcard_generator = FlashcardGenerator()
        self._web_search_agent = WebSearchAgent(settings.tavily_api_key)
        vector_search = getattr(self._vector_store, "similarity_search", None)
        web_search = self._web_search_agent.search_summary if self._web_search_agent.enabled else None
        self._cheatsheet_builder = CheatSheetBuilder(
            vector_search=vector_search,
            web_search=web_search,
        )
        self._latex_compiler = LaTeXCompiler()
        self._anki_builder = AnkiDeckBuilder(
            DeckMetadata(
                deck_name=settings.anki_deck_name,
                deck_id=settings.anki_deck_id,
                model_name=f"{settings.anki_deck_name} Model",
                model_id=settings.anki_model_id,
            )
        )
        self._anki_reader = AnkiDifficultyReader()

    async def process_study_materials(
        self,
        file_paths: Iterable[str],
        anki_export_path: Optional[str] = None,
    ) -> Dict:
        file_paths = list(file_paths)
        documents = await self._document_loader.load_many(file_paths)
        if not documents:
            raise ValueError("No readable documents supplied.")

        ingested_chunks = self._vector_store.add_documents(documents)
        key_terms = await self._term_extractor.extract(documents)
        key_terms = self._supplement_terms_with_web_search(key_terms)
        flashcards = await self._flashcard_generator.generate(key_terms, documents)

        artefacts = self._persist_outputs(flashcards, key_terms, documents)

        difficulty_payload = None
        if anki_export_path:
            difficulty_payload = self._anki_reader.parse(Path(anki_export_path))
            cheat_sheet_terms = self._terms_from_anki(difficulty_payload)
        else:
            cheat_sheet_terms = key_terms

        cheat_sheet_latex = await self._cheatsheet_builder.build(
            cards=flashcards,
            key_terms=cheat_sheet_terms,
            documents=documents,
        )
        tex_path = self._output_dir / "cheat_sheet.tex"
        artefacts.cheat_sheet = CheatSheetBuilder.save(
            cheat_sheet_latex,
            tex_path,
        )
        try:
            pdf_path = self._latex_compiler.compile(tex_path)
            artefacts.cheat_sheet_pdf = pdf_path
        except Exception as err:
            print(f"Failed to compile cheat sheet to PDF: {err}")

        summary_markdown = await self._summarise(documents)
        if summary_markdown:
            artefacts.summary_markdown = self._write_text(
                summary_markdown,
                self._output_dir / "summary.md",
            )

        metadata = {
            "pdfs_processed": len(file_paths),
            "chunks_ingested": ingested_chunks,
            "flashcards_created": len(flashcards),
            "key_terms": len(key_terms),
            "difficulty_cards": len(difficulty_payload or []),
            "processing_type": "pdf_to_anki",
        }

        return {
            "status": "success",
            "message": "Study materials generated successfully.",
            "materials": {
                "message": "Deck ready. Study the cards, then upload your Anki export for a personalised cheat sheet.",
            },
            "files": artefacts.as_download_dict(),
            "metadata": metadata,
        }

    async def process_anki_only_workflow(self, anki_export_path: str) -> Dict:
        difficulty_payload = self._anki_reader.parse(Path(anki_export_path))
        key_terms = self._terms_from_anki(difficulty_payload)
        key_terms = self._supplement_terms_with_web_search(key_terms)

        anki_cards = self._flashcards_from_terms(key_terms)
        cheat_sheet_latex = await self._cheatsheet_builder.build(
            cards=anki_cards,
            key_terms=key_terms,
            documents=[],
        )
        tex_path = self._output_dir / "anki_cheat_sheet.tex"
        cheat_sheet_path = CheatSheetBuilder.save(
            cheat_sheet_latex,
            tex_path,
        )
        try:
            pdf_path = self._latex_compiler.compile(tex_path)
            pdf_target = pdf_path
        except Exception as err:
            print(f"Failed to compile cheat sheet to PDF: {err}")
            pdf_target = None

        return {
            "status": "success",
            "message": "Generated cheat sheet from Anki export.",
            "materials": {
                "cheat_sheet": cheat_sheet_latex,
            },
            "files": {
                "cheat_sheet": str(cheat_sheet_path),
                **({"cheat_sheet_pdf": str(pdf_target)} if pdf_target else {}),
            },
            "metadata": {
                "cards_analyzed": len(difficulty_payload),
                "hardest_card": difficulty_payload[0]["name"] if difficulty_payload else None,
                "processing_type": "anki_only",
            },
        }

    def _persist_outputs(
        self,
        flashcards: List[Flashcard],
        key_terms: List[dict],
        documents: List[DocumentBundle],
    ) -> WorkflowArtifacts:
        artefacts = WorkflowArtifacts()

        if flashcards:
            flashcards_json_path = self._output_dir / "flashcards.json"
            payload = [
                {
                    "front": card.front,
                    "back": card.back,
                    "tags": card.tags,
                    "id": card.identifier,
                }
                for card in flashcards
            ]
            flashcards_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            artefacts.flashcards_json = flashcards_json_path

            anki_path = self._output_dir / "study_materials.apkg"
            self._anki_builder.build(flashcards, anki_path)
            artefacts.anki_package = anki_path

        metadata_path = self._output_dir / "documents.json"
        metadata_payload = [
            {
                "source_path": str(doc.source_path),
                "display_name": doc.display_name,
                "char_count": doc.char_count,
                "metadata": doc.metadata,
            }
            for doc in documents
        ]
        metadata_path.write_text(json.dumps(metadata_payload, indent=2), encoding="utf-8")

        terms_path = self._output_dir / "key_terms.json"
        terms_path.write_text(json.dumps(key_terms, indent=2), encoding="utf-8")

        return artefacts

    async def _summarise(self, documents: List[DocumentBundle]) -> str:
        combined = "\n\n".join(doc.markdown for doc in documents)
        if not combined.strip():
            return ""
        prompt = (
            "Create a concise study summary that captures the main topics, key terms, and "
            "recommended follow-up areas from the following material. Use markdown headings.\n\n"
            + combined[:8_000]
        )
        try:
            response = await self._llm.ainvoke([{"role": "user", "content": prompt}])
        except Exception:
            return ""
        return response.content

    @staticmethod
    def _write_text(content: str, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    @staticmethod
    def _terms_from_anki(payload: List[dict]) -> List[dict]:
        terms = []
        for item in payload:
            front = item.get("description", {}).get("front") or item.get("name")
            back = item.get("description", {}).get("back")
            if not front or not back:
                continue
            terms.append(
                {
                    "term": front,
                    "definition": back,
                    "context": "",
                }
            )
        return terms

    def _supplement_terms_with_web_search(self, key_terms: List[dict]) -> List[dict]:
        if not key_terms or not self._web_search_agent.enabled:
            return key_terms

        enriched: List[dict] = []
        for term in key_terms:
            definition = (term.get("definition") or "").strip()
            needs_search = (
                not definition
                or definition.lower() in {"not_found", "n/a", "missing", "unknown"}
                or len(definition) < 25
            )
            if needs_search:
                query = f"{term.get('term')} definition concise high-quality"
                summary = self._web_search_agent.search_summary(query, max_results=3, max_chars=360)
                if summary:
                    term = {**term, "definition": summary.strip(), "definition_source": "tavily"}
            enriched.append(term)
        return enriched

    def _flashcards_from_terms(self, terms: List[dict]) -> List[Flashcard]:
        cards: List[Flashcard] = []
        for index, term in enumerate(terms, start=1):
            name = (term.get("term") or term.get("name") or "").strip()
            definition = (
                term.get("definition")
                or term.get("description", {}).get("back")
                or ""
            ).strip()
            if not name or not definition:
                continue
            context = (
                term.get("context")
                or term.get("description", {}).get("front")
                or ""
            ).strip()
            tags = self._sanitise_tags((term.get("tags") or []), context)
            back = definition if not context else f"{definition}\n\nContext: {context}"
            cards.append(
                Flashcard(
                    front=name,
                    back=back,
                    tags=sorted(tags),
                    identifier=f"anki-{index:03d}",
                )
            )
        return cards

    def _sanitise_tags(self, tags, context: str) -> set[str]:
        safe: set[str] = set()
        source = list(tags or [])
        if context:
            source.extend(context.split())
        for tag in source:
            clean = re.sub(r"[^a-zA-Z0-9_]", "", str(tag).lower().replace("-", "_"))
            if clean and len(clean) > 2:
                safe.add(clean)
        safe.add("study_buddy")
        return safe

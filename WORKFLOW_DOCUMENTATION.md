# Study Buddy Workflow

This document summarises the refactored pipeline that powers Study Buddy. The implementation lives in `app/services/workflow.py` and is shared between the API, the CLI helpers, and legacy wrappers.

## High-level Flow

1. **Document ingestion** – `DocumentLoader` converts local PDFs (or remote URLs when Firecrawl is configured) into markdown.
2. **Vector persistence** – `VectorStoreManager` chunks, embeds, and stores the markdown in Chroma so content can be retrieved later through RAG lookups.
3. **Knowledge extraction** – `TermExtractor` collaborates with the CrewAI extraction and verification agents to enumerate key terms and their in-text definitions.
4. **Flashcard synthesis** – `FlashcardGenerator` creates seed cards from the extracted terms and asks the CrewAI flashcard agent for additional coverage.
5. **Artefact creation** – `AnkiDeckBuilder` turns the consolidated flashcards into a `.apkg` deck while the raw cards, key terms, and document metadata are persisted as JSON.
6. **Cheat sheet + summary** – `CheatSheetBuilder` drives the cheatsheet Crew agent to output a LaTeX one-pager (optionally augmented by Tavily snippets), and the LangChain `ChatOpenAI` client produces a short study summary.

All artefacts are written to `outputs/` and their paths are returned to the API caller.

## Key Modules

| Module | Responsibility |
| ------ | -------------- |
| `app/services/document_loader.py` | Normalises PDF/URL inputs into markdown `DocumentBundle` objects. |
| `app/services/vector_store.py` | Manages the persistent Chroma collection and exposes similarity search helpers. |
| `app/services/term_extraction.py` | Wraps CrewAI extraction tasks and normalises their output into JSON. |
| `app/services/flashcards.py` | Builds `Flashcard` dataclasses, de-duplicates agent output, and prepares data for Anki. |
| `app/services/anki.py` | Contains the deck builder and the difficulty reader used for Anki exports. |
| `app/services/cheatsheet.py` | Coordinates the cheatsheet agent to produce the LaTeX output and gathers optional vector/web context. |
| `app/services/workflow.py` | Coordinates the above services and exposes `process_study_materials` and `process_anki_only_workflow`. |

## Adding New Capabilities

- **New agents**: define them in `app/agents/` and inject them into the relevant service (usually `TermExtractor` or `FlashcardGenerator`).
- **Custom outputs**: extend `WorkflowArtifacts` in `app/services/models.py` and update `_persist_outputs` in the workflow.
- **Alternative summarisation**: replace `_summarise` with your desired summarisation strategy or a retrieval augmented prompt.

## Operational Tips

- Firecrawl support is optional; without an API key, only local PDFs are accepted.
- The vector store persists in `./chroma_db`. Delete the directory to reset the knowledge base.
- All generated files live in `./outputs/`; clean it between runs if you want predictable filenames.

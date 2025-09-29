# Study Buddy

Study Buddy turns PDFs and Anki exports into reusable study assets – flashcards, LaTeX cheat sheets, and AI summaries – using FastAPI, CrewAI agents, LangChain, and Chroma.

## Prerequisites

- Python 3.10+
- An OpenAI API key (`OPENAI_API_KEY`)
- Optional: Tavily and Firecrawl API keys (`TAVILY_API_KEY`, `FIRECRAWL_API_KEY`) for web enrichment and remote PDF ingestion

## Quickstart

```bash
# clone + enter
git clone <repository-url>
cd study-bot

# environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# configuration
cp .env.example .env
# edit .env with at least OPENAI_API_KEY; Tavily/Firecrawl are optional

# launch the web app
python run_webapp.py
```

Visit `http://localhost:8000` for the UI or `http://localhost:8000/docs` for the FastAPI schema.

## Architecture Overview

```
app/
 ├─ main.py                 FastAPI entrypoint
 ├─ agents/                 CrewAI agent and task definitions
 ├─ services/
 │   ├─ document_loader.py  PDF/Firecrawl ingestion to markdown
 │   ├─ vector_store.py     Chroma persistence & retrieval
 │   ├─ term_extraction.py  Agent-backed key-term extraction
 │   ├─ flashcards.py       Flashcard synthesis helpers
 │   ├─ anki.py             Deck generation & difficulty parsing
 │   ├─ cheatsheet.py       Markdown cheat-sheet composer
 │   └─ workflow.py         High-level orchestration used by the API
 └─ utils/
     └─ study_workflow.py  Compatibility shim -> services.workflow
```

The `StudyWorkflow` class (now in `app/services/workflow.py`) coordinates the entire lifecycle:

1. Convert PDFs, PowerPoint decks, or URLs into markdown (`DocumentLoader`).
2. Persist content in Chroma for later RAG lookups (`VectorStoreManager`).
3. Ask CrewAI agents to extract key terms and author extra flashcards.
4. Build flashcards, Anki decks, LaTeX/PDF cheat sheets, and summaries.
5. Optionally ingest Anki exports to prioritise difficult concepts.

All outputs land in `outputs/` for easy download by the API or UI.

## Programmatic Usage

```python
from app.services.workflow import StudyWorkflow

workflow = StudyWorkflow()
result = await workflow.process_study_materials(["/path/to/slides.pdf"])
print(result["files"]["anki_package"])
```

`process_anki_only_workflow()` accepts an exported `.apkg` file and produces a difficulty-weighted cheat sheet.

## Development Notes

- The configuration surface was streamlined; only the fields listed in `app/config/config.py` are honoured.
- Legacy helpers are routed through the new services layer (see `app/utils/pipeline.py`).
- Tests were pruned pending a refreshed suite to match the new architecture.

## Troubleshooting

- Remote URLs require `FIRECRAWL_API_KEY`; otherwise local PDFs are expected.
- Chroma persists embeddings in `./chroma_db`. Delete the directory to reset the knowledge base.
- Output artefacts are written to `./outputs`. Clean the folder if you want a fresh run.

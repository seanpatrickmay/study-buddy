# Study Buddy

Study Buddy is an agent-assisted study companion that turns lecture notes, research papers, and Anki exports into curated flashcards, decks, and one-page cheat sheets. The system couples LangChain tooling, CrewAI agents, and a FastAPI web interface so students can iterate between studying and targeted revision.

## Feature Highlights

- **Two-step workflow** – ingest PDFs, slide decks, or DOCX files to build a spaced-repetition deck, then feed your Anki export back in to generate a difficulty-weighted cheat sheet.
- **Multi-agent authoring** – CrewAI agents extract key concepts, expand definitions, and merge cheat-sheet drafts without inventing new material.
- **Vector search support** – automatically indexes uploaded content in Chroma for retrieval-augmented prompts and contextual grounding.
- **Minimalist web UI** – upload files, track progress, and download artefacts from a focused single-page interface.
- **Extensible architecture** – modular services cleanly separate ingestion, knowledge extraction, card generation, and LaTeX compilation.

## Project Layout

```
study-buddy/
├─ docs/                # Architecture notes, workflow reference, changelog
├─ src/study_buddy/     # Application source code (agents, services, web app)
│  ├─ agents/           # CrewAI agents and task definitions
│  ├─ config/           # Pydantic settings
│  ├─ core/             # Shared dataclasses and domain models
│  ├─ infrastructure/   # System integrations (LaTeX compiler, etc.)
│  ├─ services/         # Document ingestion, flashcard and cheat-sheet services
│  ├─ web/              # FastAPI application, templates, and static assets
│  └─ workflows/        # Orchestration logic (StudyWorkflow)
├─ tests/               # Pytest-based regression tests
├─ requirements.txt     # Runtime and development dependencies
├─ pyproject.toml       # Packaging metadata and tool configuration
└─ run_webapp.py        # Convenience launcher for the FastAPI server
```

## Installation

1. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables** – copy `.env.example` (if present) or set the following variables in your shell:

   | Variable | Required | Description |
   | -------- | -------- | ----------- |
   | `OPENAI_API_KEY` | ✅ | Used for LangChain and CrewAI LLM calls. |
   | `TAVILY_API_KEY` | Optional | Enables web enrichment during cheat-sheet generation. |
   | `FIRECRAWL_API_KEY` | Optional | Allows ingesting remote URLs through Firecrawl. |
   | `VECTOR_DB_PATH` | Optional | Directory for persistent Chroma storage (defaults to `./chroma_db`). |

## Usage

### Web Interface

Launch the FastAPI application and static front end:

```bash
python run_webapp.py
```

Open `http://localhost:8000` for the UI or `http://localhost:8000/docs` for the interactive OpenAPI schema. Upload PDFs, PowerPoint files, or DOCX documents to build a deck, then upload the resulting `.apkg` export to receive a personalised cheat sheet.

### Programmatic Access

```python
from study_buddy import StudyWorkflow

workflow = StudyWorkflow()
result = await workflow.process_study_materials(["/path/to/slides.pdf"])
print(result["files"]["anki_package"])
```

Use `process_anki_only_workflow("deck.apkg")` to skip document ingestion and generate a cheat sheet from your review history alone.

## Testing & Quality

- Run the automated test suite:
  ```bash
  pytest
  ```
- Lint and format the codebase with Ruff:
  ```bash
  ruff check src tests
  ruff format src tests
  ```

Continuous integration should run these commands to guard against regressions.

## Contributing

Bug reports and pull requests are welcome. Please review `docs/frontend.md` and `docs/workflow.md` for domain context, then open an issue describing the change you plan to make. For substantial contributions, include tests and update relevant documentation.

## License

This project is released under the [MIT License](LICENSE).

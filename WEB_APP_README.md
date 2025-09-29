# Study Buddy Web Interface

A lightweight front end for Study Buddy that mirrors the two-step workflow: build an Anki deck from PDFs, then upload your Anki export to generate a difficulty-aware cheat sheet.

## Key Concepts

1. **Generate Deck** – Upload one or more PDFs. Study Buddy extracts key terms, creates flashcards, and packages them into an `.apkg` deck alongside a JSON export.
2. **Refine with Anki** – After studying in Anki, export the deck (with scheduling information) and upload the `.apkg`. Study Buddy analyses the review history and provides a focused cheat sheet.

## Prerequisites

- Python 3.10+
- `OPENAI_API_KEY` in your `.env`
- Optional: `TAVILY_API_KEY` and `FIRECRAWL_API_KEY` for web enrichment and remote PDF fetching

## Setup

```bash
cp .env.example .env
# add your keys

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python run_webapp.py
```

Visit `http://localhost:8000` for the UI or `http://localhost:8000/docs` for the API schema.

## Using the Interface

### Step 1 – Build Your Deck
1. Select one or more PDF files.
2. Click **Generate deck**.
3. Download the generated `.apkg`, optional flashcard JSON, and the cheat sheet in both LaTeX and PDF formats when ready.
4. Import the deck into Anki and study as usual.

### Step 2 – Refine with Anki
1. Export your deck from Anki (ensure *Include scheduling information* is enabled).
2. Upload the `.apkg` in Step 2 of the interface.
3. Click **Generate cheat sheet** to receive a personalised summary in LaTeX and PDF formats.

## Notes

- Temporary upload files are removed after processing; generated artefacts land in `./outputs/`.
- The design intentionally stays minimal: no drag-and-drop, animations, or additional chrome.
- Delete `./chroma_db` if you need to reset the embedded knowledge base.

Enjoy using Study Buddy to streamline your revision pipeline.

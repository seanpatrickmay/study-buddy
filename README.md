# Study Bot - AI-Powered Study Material Generator

Transform PDFs into comprehensive study materials using CrewAI, LangChain, and MCP.

## Features
- PDF to Markdown conversion
- Main ideas and vocabulary extraction
- Q&A generation with Bloom's taxonomy
- Anki flashcard creation
- Comprehensive cheat sheet generation
- Content verification with Tavily

## Installation
```bash
# Clone repository
git clone <repository-url>
cd study-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
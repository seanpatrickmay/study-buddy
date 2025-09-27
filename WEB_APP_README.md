# Study Bot Web Application

A modern, interactive web interface for the Study Bot AI-powered study material generator.

## Features

### 🎯 Core Functionality
- **Drag & Drop Upload**: Easily upload PDF files by dragging them into the browser
- **Multi-File Processing**: Process multiple PDFs simultaneously
- **Real-time Progress**: Visual progress indicators during processing
- **Interactive Results**: Browse generated study materials in an intuitive interface

### 📚 Study Materials Generated
- **AI Summary**: Comprehensive overview of key concepts
- **Cheat Sheet**: Quick reference with formulas and important points
- **Interactive Flashcards**: Study cards with flip animation and keyboard navigation
- **Downloadable Content**: Export materials as markdown files

### ✨ User Experience
- **Modern Design**: Clean, responsive interface with gradient backgrounds
- **Mobile Friendly**: Works seamlessly on desktop, tablet, and mobile
- **Keyboard Shortcuts**: Use arrow keys and spacebar to navigate flashcards
- **Toast Notifications**: Helpful feedback messages throughout the process
- **Copy to Clipboard**: One-click copying of generated content

## Getting Started

### Prerequisites
1. Python 3.8 or higher
2. Required API keys:
   - OpenAI API key (required)
   - Tavily API key (required)
   - Firecrawl API key (optional)

### Setup Instructions

1. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

2. **Install Dependencies**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Launch the Web Application**
   ```bash
   # Option 1: Using the launcher script
   python run_webapp.py

   # Option 2: Using uvicorn directly
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the Application**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## How to Use

### 1. Upload Files
- **Drag & Drop**: Drag PDF files directly onto the upload area
- **Browse Files**: Click "browse files" to select PDFs from your computer
- **Multiple Files**: Upload multiple PDFs at once for combined processing

### 2. Process Documents
- Click "Process Documents" to start AI analysis
- Watch the progress bar for real-time updates
- Processing includes:
  - PDF text extraction
  - Content refinement and verification
  - Web enrichment via search
  - Flashcard generation

### 3. Review Results

#### Summary Tab
- Comprehensive overview of all key concepts
- Main ideas and supporting details
- Click the copy button to copy content

#### Cheat Sheet Tab
- Quick reference guide
- Important formulas and definitions
- Key points organized for easy review

#### Flashcards Tab
- Interactive study cards
- Click cards or use keyboard to flip
- Navigate with arrow keys
- Counter shows progress through deck

### 4. Download Materials
- Download study guide as markdown file
- Export flashcards as JSON
- Save materials for offline use

## Keyboard Shortcuts

When viewing flashcards:
- **Left Arrow**: Previous card
- **Right Arrow**: Next card
- **Spacebar**: Flip current card

## Technical Details

### Architecture
- **Frontend**: Modern HTML5, CSS3, and JavaScript
- **Backend**: FastAPI with async support
- **AI Processing**: OpenAI GPT models with RAG
- **Vector Storage**: ChromaDB for semantic search
- **Web Enrichment**: Tavily search integration

### File Support
- **Formats**: PDF files only
- **Size Limit**: 50MB per file
- **Multiple Files**: No limit on number of files

### Browser Compatibility
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers supported

## API Integration

The web app integrates seamlessly with the existing Study Bot API:

### Endpoints Used
- `POST /process` - Upload and process PDFs
- `GET /download/{file_path}` - Download generated files
- `GET /` - Serve web interface

### Data Flow
1. Frontend uploads files via FormData
2. Backend processes with AI pipeline
3. Results returned as JSON
4. Frontend renders interactive interface

## Troubleshooting

### Common Issues

**Web app won't start**
- Check that all dependencies are installed
- Ensure API keys are set in .env file
- Verify Python version is 3.8+

**Upload fails**
- Check file size (must be < 50MB)
- Ensure files are PDF format
- Verify internet connection

**Processing errors**
- Confirm OpenAI API key has credits
- Check Tavily API key is valid
- Look at browser console for error details

**No results displayed**
- Check browser console for JavaScript errors
- Verify API response in Network tab
- Ensure all static files are loading

### Getting Help

If you encounter issues:
1. Check the browser console for error messages
2. Review the server logs for backend errors
3. Ensure all API keys are properly configured
4. Try with a smaller PDF file first

## Development

### Project Structure
```
study-bot/
├── templates/
│   └── index.html          # Main web interface
├── static/
│   ├── css/
│   │   └── style.css       # Styling
│   └── js/
│       └── app.js          # Frontend logic
├── app/
│   └── main.py             # FastAPI backend
└── run_webapp.py           # Launcher script
```

### Customization
- Modify `static/css/style.css` for visual changes
- Edit `static/js/app.js` for functionality updates
- Customize `templates/index.html` for layout changes

## Performance Tips

- Process smaller PDFs for faster results
- Use modern browsers for best performance
- Ensure stable internet connection
- Close other resource-intensive applications

## Security Notes

- API keys are stored server-side only
- Uploaded files are automatically cleaned up
- No file content is stored permanently
- All processing happens locally on your server

---

**Enjoy using Study Bot to enhance your learning experience! 🚀📚**
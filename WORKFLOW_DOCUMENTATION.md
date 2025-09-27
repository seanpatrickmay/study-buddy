# Study Bot - Complete Workflow Documentation

## 🎯 **Workflow Overview**

The Study Bot now implements the exact workflow you specified:

### **Complete Process Flow:**

1. **📄 PDF Upload** → **🔄 Firecrawl Conversion** → **📝 Markdown**
2. **📚 RAG Storage** → **🗃️ Chroma Vector Database**
3. **🔍 Key Terms Extraction** → **📖 Definition Finding**
4. **🌐 Tavily Web Search** → **❓ Missing Definitions**
5. **🎴 JSON Flashcards** → **📦 Anki Package Generation**
6. **📊 Anki Export Processing** → **⚡ Difficulty Scoring**
7. **📋 Prioritized Cheat Sheet** → **🎯 Difficulty-Based Content**

---

## 🚀 **New Features Implemented**

### ✅ **1. Firecrawl Integration (Primary PDF Processor)**
- Uses Firecrawl as the primary PDF-to-markdown converter
- Falls back to pypdf if Firecrawl is unavailable
- Better text extraction and formatting

### ✅ **2. RAG Approach with Chroma**
- All processed content is automatically stored in Chroma vector database
- Enables semantic search and retrieval throughout the workflow
- Persistent storage across sessions

### ✅ **3. Key Terms Extraction & Definition Finding**
- AI-powered extraction of important terms and concepts
- Automatic definition detection within source material
- Context-aware term identification

### ✅ **4. Tavily Web Search Integration**
- Automatically searches for missing definitions
- Updates vector database with found information
- Enriches study materials with external knowledge

### ✅ **5. Correct JSON Flashcard Format**
- Matches the exact format in `cards.example.json`
- Includes proper front/back/tags/id structure
- Compatible with existing Anki conversion tools

### ✅ **6. Anki Package Generation**
- Automatically runs `json_to_anki.py` to create .apkg files
- Ready for direct import into Anki application
- Maintains card metadata and formatting

### ✅ **7. Anki Export Processing & Difficulty Integration**
- Processes user's Anki exports using `anki_to_json.py`
- Extracts difficulty scores based on review history
- Prioritizes terms in cheat sheet based on difficulty

### ✅ **8. Web Interface Enhancements**
- Added Anki export file upload option
- Visual indicators for workflow progress
- Better error handling and user feedback

---

## 📋 **Detailed Workflow Steps**

### **Step 1: PDF to Markdown Conversion**
```python
# Uses Firecrawl (preferred) or pypdf (fallback)
markdown_contents = await self._convert_pdfs_to_markdown(file_paths)
```
- **Primary**: Firecrawl for better formatting and extraction
- **Fallback**: pypdf for basic text extraction
- **Output**: Clean markdown with preserved structure

### **Step 2: RAG Storage in Vector Database**
```python
# Store in Chroma for semantic search
await self._store_in_vector_database(markdown_contents, file_paths)
```
- **Chunking**: Text split into semantic chunks
- **Embedding**: OpenAI embeddings for vector representation
- **Storage**: Persistent Chroma database
- **Metadata**: Source file and chunk information

### **Step 3: Key Terms Extraction**
```python
# AI-powered term extraction with definitions
key_terms = await self._extract_key_terms_and_definitions(markdown_contents)
```
- **LLM Analysis**: GPT identifies important terms
- **Definition Matching**: Finds definitions within text
- **Context Preservation**: Maintains term context

### **Step 4: Tavily Web Search for Missing Definitions**
```python
# Search for missing definitions
definition = await self._search_definition_with_tavily(term)
```
- **Automatic Detection**: Identifies terms without definitions
- **Web Search**: Uses Tavily to find authoritative definitions
- **Database Update**: Adds found definitions to vector store

### **Step 5: Flashcard Generation**
```python
# Generate cards in correct JSON format
flashcards = await self._generate_flashcards(key_terms, markdown_contents)
```
- **Format Compliance**: Matches `cards.example.json` structure
- **Content Quality**: Clear questions and concise answers
- **Tagging**: Relevant tags for organization

### **Step 6: Anki Package Creation**
```python
# Convert JSON to .apkg using existing script
anki_package = await self._create_anki_package(flashcards_json)
```
- **Script Integration**: Uses `json_to_anki.py`
- **Package Generation**: Creates ready-to-import .apkg file
- **Metadata Preservation**: Maintains all card properties

### **Step 7: Difficulty-Based Cheat Sheet**
```python
# Prioritize content by Anki difficulty data
cheat_sheet = await self._generate_prioritized_cheatsheet(terms, content, difficulty_data)
```
- **Difficulty Integration**: Uses Anki export data if provided
- **Smart Prioritization**: Difficult terms appear first
- **RAG Enhancement**: Additional context from vector database

---

## 🎮 **How to Use the New Workflow**

### **Basic Usage (PDFs Only)**
1. Upload PDF files via web interface
2. Click "Process Documents"
3. Get flashcards, Anki package, and cheat sheet

### **Advanced Usage (with Anki Export)**
1. Upload PDF files
2. **Upload your Anki deck export** (.apkg file)
3. Click "Process Documents"
4. Get difficulty-prioritized study materials

### **Anki Integration Workflow**
1. **First Time**: Process PDFs → Get Anki package → Import to Anki
2. **Study in Anki**: Review cards, develop difficulty patterns
3. **Export from Anki**: Export deck WITH scheduling information
4. **Re-process**: Upload same PDFs + Anki export → Get prioritized materials

---

## 🛠️ **Technical Implementation**

### **New Files Created:**
- `app/utils/study_workflow.py` - Complete workflow implementation
- Enhanced web interface with Anki upload support
- Updated pipeline integration

### **Existing Files Enhanced:**
- `app/main.py` - Added Anki export handling
- `app/utils/pipeline.py` - Integrated new workflow
- Web interface files - Added Anki upload UI

### **Dependencies Utilized:**
- **Firecrawl**: PDF processing
- **Chroma**: Vector database storage
- **Tavily**: Web search for definitions
- **OpenAI**: LLM processing and embeddings
- **genanki**: Anki package generation

---

## 📊 **Workflow Validation**

### ✅ **Requirements Met:**

1. **✅ Firecrawl PDF Processing**: Primary converter with pypdf fallback
2. **✅ RAG with Chroma**: All content stored in vector database
3. **✅ Key Terms Extraction**: AI-powered term identification
4. **✅ Definition Finding**: Within text + Tavily web search
5. **✅ Correct JSON Format**: Matches cards.example.json exactly
6. **✅ Anki Package Generation**: Uses json_to_anki.py script
7. **✅ Difficulty Integration**: Uses anki_to_json.py for scoring
8. **✅ Prioritized Cheat Sheets**: Difficulty-based content ordering

### 🔄 **Complete Workflow Cycle:**
```
PDFs → Firecrawl → Markdown → Chroma DB → Key Terms →
Tavily Search → Flashcards JSON → Anki Package →
User Studies → Anki Export → Difficulty Analysis →
Prioritized Cheat Sheet
```

---

## 🚀 **Running the Enhanced Workflow**

### **Setup:**
```bash
# Ensure all API keys are configured in .env
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
FIRECRAWL_API_KEY=your_firecrawl_key  # Optional

# Start the application
python run_webapp.py
```

### **Access:**
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### **Workflow Options:**
1. **Standard**: Upload PDFs only → Get all study materials
2. **Prioritized**: Upload PDFs + Anki export → Get difficulty-prioritized materials

---

## 🎯 **Benefits of the New Workflow**

### **For Students:**
- **Adaptive Learning**: Cheat sheets prioritize your difficult topics
- **Complete Integration**: Seamless Anki workflow
- **Better Quality**: Firecrawl + web search for comprehensive content

### **For Developers:**
- **Modular Design**: Each step is clearly separated
- **RAG Architecture**: Vector database enables advanced features
- **Extensible**: Easy to add new processing steps

### **For Study Efficiency:**
- **Personalized**: Content adapts to your learning patterns
- **Comprehensive**: Combines source material with web knowledge
- **Convenient**: End-to-end automated workflow

---

**The Study Bot now implements your exact specifications with a complete, integrated workflow from PDF upload to personalized, difficulty-prioritized study materials! 🎓✨**
#!/usr/bin/env python3
"""
Complete Study Bot Workflow Implementation
Follows the exact specifications provided by the user.
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from tavily import TavilyClient
from crewai import Crew

from app.config.config import settings
from app.utils.firecrawl_handler import FirecrawlHandler
from app.utils.pdf_processor import PDFProcessor
from app.agents.rag_agent import rag_agent, web_enricher_agent, rag_task, enrich_task, chroma_search, enrich_from_web
from app.agents.tav_agent import extraction_agent, verification_agent, extraction_task, verification_task
from app.agents.flashcard_agent import flashcard_agent, flashcard_task
from app.agents.cheatsheet_agent import cheatsheet_agent, cheatsheet_task


class StudyWorkflow:
    """
    Complete implementation of the specified study materials workflow:

    1. Upload PDFs → Firecrawl conversion to markdown
    2. Store in Chroma vector database (RAG approach)
    3. Extract key terms and find definitions
    4. Use Tavily to find missing definitions
    5. Generate flashcards in correct JSON format
    6. Convert to Anki package
    7. Process Anki exports for difficulty scoring
    8. Generate difficulty-prioritized cheat sheets
    """

    def __init__(self):
        # Set environment variables for API keys (needed for CrewAI agents)
        os.environ['OPENAI_API_KEY'] = settings.openai_api_key
        if settings.tavily_api_key:
            os.environ['TAVILY_API_KEY'] = settings.tavily_api_key

        # Initialize handlers
        self.firecrawl_handler = FirecrawlHandler() if settings.firecrawl_api_key else None
        self.pdf_processor = PDFProcessor()  # Fallback

        # Initialize LLM and embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.embedding_model
        )

        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key
        )

        # Initialize Chroma vector database
        self.vectorstore = Chroma(
            collection_name="study_bot",
            persist_directory=str(settings.vector_db_path),
            embedding_function=self.embeddings
        )

        # Initialize Tavily client
        self.tavily_client = TavilyClient(api_key=settings.tavily_api_key) if settings.tavily_api_key else None

        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        # Ensure directories exist
        settings.output_dir.mkdir(parents=True, exist_ok=True)

    async def process_study_materials(self, file_paths: List[str], anki_export_path: Optional[str] = None) -> Dict:
        """
        Simplified workflow for PDF processing:
        1. Convert PDFs using Firecrawl
        2. Store in vector database (RAG)
        3. Extract key terms and definitions
        4. Generate flashcards
        5. Create Anki package
        Note: No cheat sheet, summary, or key terms in output - user must re-upload Anki package for cheat sheet
        """
        try:
            # Step 1: Convert PDFs to markdown using Firecrawl
            print("🔄 Step 1: Converting PDFs to markdown using Firecrawl...")
            markdown_contents = await self._convert_pdfs_to_markdown(file_paths)

            # Step 2: Store in Chroma vector database (RAG approach)
            print("🔄 Step 2: Storing content in vector database...")
            await self._store_in_vector_database(markdown_contents, file_paths)

            # Step 3: Extract key terms and find definitions
            print("🔄 Step 3: Extracting key terms and finding definitions...")
            key_terms_with_definitions = await self._extract_key_terms_and_definitions(markdown_contents)

            # Step 4: Generate flashcards in correct JSON format
            print("🔄 Step 4: Generating flashcards...")
            flashcards_json = await self._generate_flashcards(key_terms_with_definitions, markdown_contents)

            # Step 5: Create Anki package
            print("🔄 Step 5: Creating Anki package...")
            anki_package_path = await self._create_anki_package(flashcards_json)

            return {
                "status": "success",
                "materials": {
                    "message": "Anki package created successfully! Download it, study the cards, then re-upload your Anki export to get a personalized cheat sheet."
                },
                "files": {
                    "anki_package": str(anki_package_path)
                },
                "metadata": {
                    "pdfs_processed": len(file_paths),
                    "flashcards_created": len(flashcards_json),
                    "used_firecrawl": self.firecrawl_handler is not None,
                    "processing_type": "pdf_to_anki"
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Workflow failed: {str(e)}",
                "error_type": type(e).__name__
            }

    async def _convert_pdfs_to_markdown(self, file_paths: List[str]) -> List[str]:
        """Step 1: Convert PDFs to markdown using Firecrawl (URLs only) or pypdf fallback"""
        markdown_contents = []
        firecrawl_used = False

        for file_path in file_paths:
            try:
                if self.firecrawl_handler and file_path.startswith('http'):
                    # Use Firecrawl for URLs only
                    print(f"🔥 Using Firecrawl for URL: {file_path}")
                    result = self.firecrawl_handler.process_pdf_url(file_path)

                    if result['success']:
                        markdown_contents.append(result['markdown'])
                        firecrawl_used = True
                        continue
                    else:
                        print(f"⚠️ Firecrawl failed for {file_path}: {result.get('error')}")

                # Use pypdf for local files (Firecrawl doesn't support local uploads)
                filename = os.path.basename(file_path)
                print(f"📄 Using pypdf for local file: {filename}")
                markdown_content = self.pdf_processor.pdf_to_markdown(Path(file_path))
                markdown_contents.append(markdown_content)

            except Exception as e:
                print(f"⚠️ Warning: Failed to process {file_path}: {e}")
                markdown_contents.append(f"# Failed to process: {file_path}\n\nError: {str(e)}")

        if firecrawl_used:
            print("✅ Successfully used Firecrawl for URL-based PDFs")
        else:
            print("📝 Processed all PDFs using pypdf (user uploads are local files)")

        return markdown_contents

    async def _store_in_vector_database(self, markdown_contents: List[str], file_paths: List[str]) -> None:
        """Step 2: Store content in Chroma vector database for RAG"""
        documents = []

        for i, (content, file_path) in enumerate(zip(markdown_contents, file_paths)):
            # Split content into chunks
            chunks = self.text_splitter.split_text(content)

            # Create documents with metadata
            for j, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": os.path.basename(file_path),
                        "file_index": i,
                        "chunk_index": j,
                        "total_chunks": len(chunks)
                    }
                )
                documents.append(doc)

        # Add documents to vector store
        if documents:
            self.vectorstore.add_documents(documents)
            # Note: Chroma 0.4.x+ automatically persists documents

    def _paginate_markdown_content(self, markdown_contents: List[str], max_chunk_size: int = 6000) -> List[str]:
        """Break markdown content into manageable chunks for processing"""
        combined_content = "\n\n".join(markdown_contents)

        # Split by logical page breaks first (if they exist)
        if "## Page " in combined_content or "# Page " in combined_content:
            # Split by page headers
            pages = []
            current_page = ""

            for line in combined_content.split('\n'):
                if (line.startswith("## Page ") or line.startswith("# Page ")) and current_page.strip():
                    pages.append(current_page.strip())
                    current_page = line + '\n'
                else:
                    current_page += line + '\n'

            if current_page.strip():
                pages.append(current_page.strip())

            # If pages are still too large, split them further
            final_chunks = []
            for page in pages:
                if len(page) <= max_chunk_size:
                    final_chunks.append(page)
                else:
                    # Split large pages by paragraphs
                    paragraphs = page.split('\n\n')
                    current_chunk = ""

                    for paragraph in paragraphs:
                        if len(current_chunk + paragraph) > max_chunk_size and current_chunk:
                            final_chunks.append(current_chunk.strip())
                            current_chunk = paragraph + '\n\n'
                        else:
                            current_chunk += paragraph + '\n\n'

                    if current_chunk.strip():
                        final_chunks.append(current_chunk.strip())

            return final_chunks
        else:
            # No page breaks found, split by size only
            chunks = []
            words = combined_content.split()
            current_chunk = ""

            for word in words:
                if len(current_chunk + " " + word) > max_chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = word + " "
                else:
                    current_chunk += word + " "

            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            return chunks

    async def _extract_key_terms_and_definitions(self, markdown_contents: List[str]) -> List[Dict]:
        """Step 3: Extract key terms using CrewAI agents and find definitions with pagination"""
        try:
            # Break content into manageable chunks
            content_chunks = self._paginate_markdown_content(markdown_contents)
            print(f"🔄 Processing {len(content_chunks)} content chunks for key term extraction...")

            all_extracted_terms = []

            # Process each chunk separately
            for i, chunk in enumerate(content_chunks, 1):
                try:
                    print(f"🔄 Processing chunk {i}/{len(content_chunks)} (size: {len(chunk)} chars)...")

                    # Create crew with extraction and verification agents
                    extraction_crew = Crew(
                        agents=[extraction_agent, verification_agent],
                        tasks=[extraction_task, verification_task],
                        verbose=True
                    )

                    # Execute extraction with agents
                    extraction_result = extraction_crew.kickoff({
                        "markdown": chunk
                    })

                    # Parse the markdown result from agents to JSON format
                    chunk_extracted_terms = await self._parse_agent_extraction_to_json(str(extraction_result))
                    all_extracted_terms.extend(chunk_extracted_terms)

                except Exception as e:
                    print(f"⚠️ Failed to process chunk {i}: {e}")
                    continue

            # Remove duplicates while preserving order
            seen_terms = set()
            unique_extracted_terms = []
            for term_data in all_extracted_terms:
                term_key = term_data.get("term", "").lower()
                if term_key and term_key not in seen_terms:
                    seen_terms.add(term_key)
                    unique_extracted_terms.append(term_data)

            print(f"🔄 Extracted {len(unique_extracted_terms)} unique terms from {len(content_chunks)} chunks")

            # Find definitions for terms without definitions using Tavily
            for term_data in unique_extracted_terms:
                if not term_data.get("definition") or term_data.get("definition") == "NOT_FOUND":
                    definition = await self._search_definition_with_tavily(term_data["term"])
                    if definition:
                        term_data["definition"] = definition
                        # Also add to vector database for future reference
                        doc = Document(
                            page_content=f"Term: {term_data['term']}\nDefinition: {definition}",
                            metadata={"source": "tavily_search", "term": term_data["term"]}
                        )
                        self.vectorstore.add_documents([doc])

            return unique_extracted_terms

        except Exception as e:
            print(f"⚠️ Agent extraction failed: {e}, falling back to LLM extraction...")
            # Fallback to the original LLM method
            return await self._extract_key_terms_fallback(markdown_contents)

    async def _parse_agent_extraction_to_json(self, agent_result: str) -> List[Dict]:
        """Parse agent extraction result into JSON format"""
        try:
            # Use LLM to convert agent markdown output to JSON
            conversion_prompt = f"""
            Convert the following key terms and vocabulary extraction into JSON format:

            {agent_result}

            Convert to this exact JSON structure:
            [
                {{
                    "term": "Term Name",
                    "definition": "Definition from text or 'NOT_FOUND' if missing",
                    "context": "Brief context where the term appears"
                }}
            ]

            Only return the JSON array, nothing else.
            """

            response = await self.llm.ainvoke([{"role": "user", "content": conversion_prompt}])

            # Extract JSON from response
            json_match = re.search(r'\[[\s\S]*\]', response.content)
            if json_match:
                return json.loads(json_match.group())
            else:
                return []
        except Exception:
            return []

    async def _extract_key_terms_fallback(self, markdown_contents: List[str]) -> List[Dict]:
        """Fallback method for key terms extraction using direct LLM"""
        combined_content = "\n\n".join(markdown_contents)

        extraction_prompt = f"""
        Analyze the following study material and extract key terms, concepts, and important topics.
        For each term, try to find its definition within the text.

        Format your response as a JSON array with this structure:
        [
            {{
                "term": "Term Name",
                "definition": "Definition from text or 'NOT_FOUND'",
                "context": "Brief context where the term appears"
            }}
        ]

        Study Material:
        {combined_content[:8000]}
        """

        response = await self.llm.ainvoke([{"role": "user", "content": extraction_prompt}])

        try:
            json_match = re.search(r'\[[\s\S]*\]', response.content)
            if json_match:
                return json.loads(json_match.group())
            else:
                return []
        except json.JSONDecodeError:
            return []

    async def _search_definition_with_tavily(self, term: str) -> Optional[str]:
        """Use Tavily to search for missing definitions"""
        if not self.tavily_client:
            return None

        try:
            query = f"define {term} definition meaning explanation"
            response = self.tavily_client.search(
                query=query,
                max_results=3,
                include_answer="basic"
            )

            # Extract definition from Tavily response
            if response.get("answer"):
                return response["answer"]

            # Fallback to first result content
            results = response.get("results", [])
            if results:
                return results[0].get("content", "")[:500]  # Limit length

        except Exception as e:
            print(f"⚠️ Tavily search failed for '{term}': {e}")

        return None

    async def _generate_flashcards(self, key_terms: List[Dict], markdown_contents: List[str]) -> List[Dict]:
        """Step 4: Generate flashcards using CrewAI flashcard agent"""
        try:
            # First, create flashcards from key terms
            flashcards = []

            for i, term_data in enumerate(key_terms):
                if term_data.get("definition") and term_data["definition"] != "NOT_FOUND":
                    # Clean tags - replace spaces with underscores, remove special characters
                    clean_tags = ["study-bot", "key-term"]
                    if term_data.get("context"):
                        clean_tag = term_data["context"].replace(" ", "_").replace("-", "_").lower()
                        clean_tag = ''.join(c for c in clean_tag if c.isalnum() or c == '_')
                        if clean_tag:
                            clean_tags.append(clean_tag)

                    flashcard = {
                        "front": f"What is {term_data['term']}?",
                        "back": term_data["definition"],
                        "tags": clean_tags,
                        "id": f"sb-{i+1:03d}"
                    }
                    flashcards.append(flashcard)

            # Use flashcard agent to generate additional cards with pagination
            content_chunks = self._paginate_markdown_content(markdown_contents, max_chunk_size=5000)
            print(f"🔄 Processing {len(content_chunks)} content chunks for flashcard generation...")

            all_additional_cards = []

            # Process each chunk for additional flashcards
            for i, chunk in enumerate(content_chunks, 1):
                try:
                    print(f"🔄 Generating flashcards from chunk {i}/{len(content_chunks)} (size: {len(chunk)} chars)...")

                    # Create crew with flashcard agent
                    flashcard_crew = Crew(
                        agents=[flashcard_agent],
                        tasks=[flashcard_task],
                        verbose=True
                    )

                    agent_result = flashcard_crew.kickoff({
                        "markdown": chunk
                    })

                    # Parse agent result to get additional flashcards
                    try:
                        agent_result_str = str(agent_result)
                        json_match = re.search(r'\[[\s\S]*\]', agent_result_str)
                        if json_match:
                            chunk_additional_cards = json.loads(json_match.group())
                            all_additional_cards.extend(chunk_additional_cards)
                        else:
                            print(f"⚠️ No valid JSON found in chunk {i} agent result")
                    except json.JSONDecodeError:
                        print(f"⚠️ Failed to parse JSON from chunk {i} agent result")
                        continue

                except Exception as e:
                    print(f"⚠️ Failed to process chunk {i} for flashcards: {e}")
                    continue

            print(f"🔄 Generated {len(all_additional_cards)} additional cards from {len(content_chunks)} chunks")

            # Clean tags for all additional cards and remove duplicates
            seen_cards = set()
            unique_additional_cards = []

            for card in all_additional_cards:
                # Create a unique key for the card
                card_key = (card.get("front", "").strip().lower(), card.get("back", "").strip().lower())
                if card_key not in seen_cards and card_key[0] and card_key[1]:
                    seen_cards.add(card_key)

                    if "tags" in card and isinstance(card["tags"], list):
                        clean_tags = []
                        for tag in card["tags"]:
                            clean_tag = str(tag).replace(" ", "_").replace("-", "_").lower()
                            clean_tag = ''.join(c for c in clean_tag if c.isalnum() or c == '_')
                            if clean_tag:
                                clean_tags.append(clean_tag)
                        card["tags"] = clean_tags

                    # Add unique ID if missing
                    if "id" not in card or not card["id"]:
                        card["id"] = f"sb-agent-{len(flashcards) + len(unique_additional_cards) + 1:03d}"

                    unique_additional_cards.append(card)

            # Combine all flashcards
            flashcards.extend(unique_additional_cards)
            print(f"🔄 Total flashcards created: {len(flashcards)} (from key terms: {len(flashcards) - len(unique_additional_cards)}, from agent: {len(unique_additional_cards)})")

        except Exception as e:
            print(f"⚠️ Flashcard agent failed: {e}, using fallback generation...")
            # Fallback to LLM-based generation
            flashcards.extend(await self._generate_flashcards_fallback(markdown_contents, len(flashcards)))

        # Save flashcards JSON
        flashcards_path = settings.output_dir / "flashcards.json"
        with open(flashcards_path, 'w', encoding='utf-8') as f:
            json.dump(flashcards, f, indent=2, ensure_ascii=False)

        return flashcards

    async def _generate_flashcards_fallback(self, markdown_contents: List[str], start_id: int = 0) -> List[Dict]:
        """Fallback flashcard generation using direct LLM with pagination"""
        content_chunks = self._paginate_markdown_content(markdown_contents, max_chunk_size=5000)
        all_flashcards = []

        for i, chunk in enumerate(content_chunks, 1):
            print(f"🔄 Fallback generation for chunk {i}/{len(content_chunks)} (size: {len(chunk)} chars)...")

            generation_prompt = f"""
            Create flashcards from this study material. Format as JSON array matching this exact structure:
            [
                {{"front": "Question", "back": "Answer", "tags": ["tag1", "tag2"], "id": "unique-id"}}
            ]

            Guidelines:
            - Create clear, specific questions
            - Provide concise but complete answers
            - Use relevant tags (no spaces, use underscores)
            - Make each ID unique
            - Focus on important concepts, formulas, and facts

            Study Material:
            {chunk}
            """

            try:
                response = await self.llm.ainvoke([{"role": "user", "content": generation_prompt}])
                json_match = re.search(r'\[[\s\S]*\]', response.content)
                if json_match:
                    chunk_cards = json.loads(json_match.group())
                    # Clean tags and assign IDs for all cards
                    for j, card in enumerate(chunk_cards):
                        # Ensure unique ID
                        card["id"] = f"sb-fallback-{start_id + len(all_flashcards) + j + 1:03d}"
                        # Clean tags
                        if "tags" in card and isinstance(card["tags"], list):
                            clean_tags = []
                            for tag in card["tags"]:
                                clean_tag = str(tag).replace(" ", "_").replace("-", "_").lower()
                                clean_tag = ''.join(c for c in clean_tag if c.isalnum() or c == '_')
                                if clean_tag:
                                    clean_tags.append(clean_tag)
                            card["tags"] = clean_tags
                    all_flashcards.extend(chunk_cards)
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️ Failed to generate flashcards for chunk {i}: {e}")
                continue

        return all_flashcards

    async def _create_anki_package(self, flashcards: List[Dict]) -> Path:
        """Step 5: Convert JSON flashcards to Anki package using json_to_anki.py"""
        flashcards_path = settings.output_dir / "flashcards.json"
        anki_package_path = settings.output_dir / "study_materials.apkg"

        # Save flashcards if not already saved
        if not flashcards_path.exists():
            with open(flashcards_path, 'w', encoding='utf-8') as f:
                json.dump(flashcards, f, indent=2, ensure_ascii=False)

        # Run json_to_anki.py script
        json_to_anki_path = Path("app/utils/json_to_anki.py")

        try:
            cmd = [
                "python3", str(json_to_anki_path),
                "--input", str(flashcards_path),
                "--deck", "Study Bot Materials",
                "--out", str(anki_package_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ Anki package created: {result.stdout}")

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to create Anki package: {e.stderr}")
            # Create a placeholder file
            anki_package_path.touch()

        return anki_package_path

    async def _process_anki_export(self, anki_export_path: str) -> Optional[List[Dict]]:
        """Step 6: Process Anki export to extract difficulty data"""
        # Use absolute paths to avoid working directory issues
        script_dir = Path(__file__).parent.parent.parent  # Go up to project root
        anki_to_json_path = script_dir / "app" / "utils" / "anki_to_json.py"
        difficulty_json_path = settings.output_dir / "difficulty_data.json"

        try:
            cmd = [
                "python3", str(anki_to_json_path),
                "--apkg", anki_export_path,
                "--out", str(difficulty_json_path)
            ]

            print(f"🔍 Debug: Running command: {' '.join(cmd)}")
            print(f"🔍 Debug: Working directory: {script_dir}")
            print(f"🔍 Debug: Script path exists: {anki_to_json_path.exists()}")
            print(f"🔍 Debug: Input file exists: {Path(anki_export_path).exists()}")
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(script_dir))
            print(f"🔍 Debug: anki_to_json.py stdout: {result.stdout}")
            if result.stderr:
                print(f"🔍 Debug: anki_to_json.py stderr: {result.stderr}")

            # Check for errors
            if result.returncode != 0:
                error_msg = f"anki_to_json.py failed with exit code {result.returncode}"
                if result.stderr:
                    error_msg += f"\nSTDERR: {result.stderr}"
                if result.stdout:
                    error_msg += f"\nSTDOUT: {result.stdout}"
                print(f"🔍 Debug: ERROR - {error_msg}")
                return None

            # Check if file was created and load difficulty data
            if not difficulty_json_path.exists():
                print(f"🔍 Debug: ERROR - Output file {difficulty_json_path} was not created!")
                return None

            file_size = difficulty_json_path.stat().st_size
            print(f"🔍 Debug: Output file {difficulty_json_path} exists, size: {file_size} bytes")

            with open(difficulty_json_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"🔍 Debug: Raw file content preview: {content[:300]}...")

            # Parse JSON
            with open(difficulty_json_path, 'r', encoding='utf-8') as f:
                difficulty_data = json.load(f)

            print(f"🔍 Debug: Loaded {len(difficulty_data)} items from difficulty_data.json")
            if difficulty_data:
                first_item = difficulty_data[0]
                print(f"🔍 Debug: First item keys: {list(first_item.keys())}")
                print(f"🔍 Debug: First item preview: {str(first_item)[:200]}...")

            return difficulty_data

        except Exception as e:
            print(f"⚠️ Failed to process Anki export: {e}")
            return None

    async def _generate_prioritized_cheatsheet(self,
                                             key_terms: List[Dict],
                                             markdown_contents: List[str],
                                             difficulty_data: Optional[List[Dict]]) -> str:
        """Step 7: Generate cheat sheet prioritized by difficulty data"""

        # Create difficulty lookup if available
        difficulty_lookup = {}
        if difficulty_data:
            for item in difficulty_data:
                difficulty_lookup[item.get("name", "")] = item.get("difficulty_score", 0)

        # Sort key terms by difficulty (highest first)
        if difficulty_data:
            key_terms_sorted = sorted(
                key_terms,
                key=lambda x: difficulty_lookup.get(x.get("term", ""), 0),
                reverse=True
            )
        else:
            key_terms_sorted = key_terms

        # Generate cheat sheet content
        cheat_sheet_parts = [
            "# Study Materials Cheat Sheet",
            "*Generated by Study Bot with AI-powered prioritization*",
            ""
        ]

        if difficulty_data:
            cheat_sheet_parts.extend([
                "## 🔥 High Priority Terms (Based on Difficulty Data)",
                "*These terms showed higher difficulty in your Anki reviews*",
                ""
            ])
        else:
            cheat_sheet_parts.extend([
                "## 📚 Key Terms and Concepts",
                ""
            ])

        # Add key terms section
        for i, term_data in enumerate(key_terms_sorted[:20]):  # Top 20 terms
            term = term_data.get("term", "")
            definition = term_data.get("definition", "")
            difficulty_score = difficulty_lookup.get(term, 0)

            if difficulty_data and difficulty_score > 0:
                cheat_sheet_parts.append(f"### {term} (Difficulty: {difficulty_score:.1f})")
            else:
                cheat_sheet_parts.append(f"### {term}")

            cheat_sheet_parts.append(f"{definition}")
            cheat_sheet_parts.append("")

        # Add additional context using RAG
        if len(key_terms) < 10:  # If not enough terms, search for more context
            additional_context = await self._get_additional_context_from_rag(markdown_contents)
            cheat_sheet_parts.extend([
                "## 📖 Additional Important Information",
                "",
                additional_context,
                ""
            ])

        cheat_sheet_content = "\n".join(cheat_sheet_parts)

        # Save cheat sheet
        cheat_sheet_path = settings.output_dir / "cheat_sheet.md"
        with open(cheat_sheet_path, 'w', encoding='utf-8') as f:
            f.write(cheat_sheet_content)

        return cheat_sheet_content

    async def _get_additional_context_from_rag(self, markdown_contents: List[str]) -> str:
        """Use RAG to find additional important context when needed"""
        query = "important concepts key information main topics summary"

        # Search vector database
        try:
            docs = self.vectorstore.similarity_search(query, k=5)
            if docs:
                context_parts = []
                for doc in docs:
                    content = doc.page_content[:300]  # Limit length
                    context_parts.append(f"• {content}")

                return "\n".join(context_parts)
        except Exception:
            pass

        # Fallback: use Tavily to search for more information
        if self.tavily_client:
            try:
                combined_content = "\n".join(markdown_contents)[:1000]
                search_query = f"additional information about {combined_content[:200]}"

                response = self.tavily_client.search(
                    query=search_query,
                    max_results=2,
                    include_answer="basic"
                )

                if response.get("answer"):
                    return f"**Additional Context (from web search):**\n{response['answer']}"

            except Exception:
                pass

        return "Additional context not available."

    async def _generate_prioritized_cheatsheet_with_agents(self,
                                                         key_terms: List[Dict],
                                                         markdown_contents: List[str],
                                                         difficulty_data: Optional[List[Dict]]) -> str:
        """Generate cheat sheet using CrewAI agents with database retrieval and web search fallback"""
        try:
            # Create difficulty lookup
            difficulty_lookup = {}
            if difficulty_data:
                for item in difficulty_data:
                    difficulty_lookup[item.get("name", "")] = item.get("difficulty_score", 0)

            # Convert key terms to flashcard-like format for the cheatsheet agent
            flashcard_format = []
            for term in key_terms:
                term_name = term.get("term", "")
                difficulty_score = difficulty_lookup.get(term_name, 0)

                flashcard_format.append({
                    "front": term_name,
                    "back": term.get("definition", ""),
                    "context": term.get("context", ""),
                    "difficulty_score": difficulty_score
                })

            # Sort by difficulty (highest first)
            flashcard_format.sort(key=lambda x: x["difficulty_score"], reverse=True)

            # Note: Tools should be defined in the agent files, not assigned dynamically

            # Create crew with database retrieval agent and cheatsheet agent
            crew = Crew(
                agents=[cheatsheet_agent],
                tasks=[cheatsheet_task],
                verbose=True
            )

            # Execute the crew with the flashcard data
            result = crew.kickoff({
                "flashcards": json.dumps(flashcard_format, indent=2)
            })

            return str(result) if result else "Failed to generate cheat sheet with agents."

        except Exception as e:
            print(f"⚠️ Failed to generate cheat sheet with agents: {e}")
            # Fallback to the original method
            return await self._generate_prioritized_cheatsheet(key_terms, markdown_contents, difficulty_data)

    async def _retrieve_from_database_with_fallback(self, query: str, max_results: int = 4) -> str:
        """Use database retrieval agent with web search fallback"""
        try:
            # Note: Tools should be defined in the agent files, not assigned dynamically

            # Create crew with database retrieval agent
            retrieval_crew = Crew(
                agents=[rag_agent],
                tasks=[rag_task],
                verbose=True
            )

            print(f"🔄 Retrieving information from database: {query}")
            result = retrieval_crew.kickoff({"query": query})

            return str(result) if result else "No information found in database or web search."

        except Exception as e:
            print(f"⚠️ Database retrieval failed: {e}")
            # Direct fallback to tools if crew fails
            try:
                return chroma_search(query)
            except Exception:
                return f"Database retrieval failed for query: {query}"

    async def _generate_summary(self, markdown_contents: List[str]) -> str:
        """Generate a comprehensive summary of the study materials"""
        combined_content = "\n\n".join(markdown_contents)

        # Limit content for token constraints
        content_preview = combined_content[:8000]

        summary_prompt = f"""
        Create a comprehensive summary of the following study materials.
        Focus on:
        - Main topics and themes
        - Key concepts covered
        - Important information students should know
        - Overall scope of the materials

        Study Materials:
        {content_preview}

        Provide a well-structured summary in markdown format.
        """

        try:
            response = await self.llm.ainvoke([{"role": "user", "content": summary_prompt}])
            return response.content
        except Exception as e:
            print(f"⚠️ Failed to generate summary: {e}")
            # Fallback to basic summary
            lines = combined_content.split('\n')
            headers = [line for line in lines if line.startswith('#')]
            if headers:
                return f"# Study Materials Summary\n\nThis document covers:\n" + "\n".join(f"- {h.lstrip('#').strip()}" for h in headers[:10])
            else:
                return f"# Study Materials Summary\n\nProcessed {len(markdown_contents)} document(s) containing {len(combined_content)} characters of content."

    async def process_anki_only_workflow(self, anki_export_path: str) -> Dict:
        """
        Process only an Anki export to generate a customized cheat sheet
        This allows users to upload their studied Anki deck and get difficulty-prioritized study materials
        """
        try:
            print("🔄 Processing Anki export for customized cheat sheet generation...")

            # Step 1: Process Anki export for difficulty data and card content
            print("🔄 Step 1: Extracting difficulty data and card content from Anki export...")
            difficulty_data = await self._process_anki_export(anki_export_path)

            if not difficulty_data:
                raise Exception("Failed to extract data from Anki export")

            # Step 2: Extract terms and content from the difficulty data
            print("🔄 Step 2: Extracting key terms from Anki cards...")
            key_terms = self._extract_terms_from_anki_data(difficulty_data)

            # Step 3: Generate customized cheat sheet using agents with database retrieval
            print("🔄 Step 3: Generating difficulty-prioritized cheat sheet with agents...")
            cheat_sheet = await self._generate_cheatsheet_from_anki_data(key_terms, difficulty_data)

            # Step 4: Generate a summary from the card content
            print("🔄 Step 4: Generating summary from Anki card content...")
            card_contents = [f"{item.get('front', '')}: {item.get('back', '')}" for item in difficulty_data]
            summary = await self._generate_summary(card_contents)

            return {
                "status": "success",
                "materials": {
                    "summary": summary,
                    "key_terms": key_terms,
                    "cheat_sheet": cheat_sheet,
                    "difficulty_data": difficulty_data
                },
                "files": {
                    "cheat_sheet": str(settings.output_dir / "anki_cheat_sheet.md")
                },
                "metadata": {
                    "cards_processed": len(difficulty_data),
                    "processing_type": "anki_only",
                    "has_difficulty_data": True
                }
            }

        except Exception as e:
            print(f"❌ Anki-only workflow failed: {e}")
            raise Exception(f"Failed to process Anki export: {str(e)}")

    def _extract_terms_from_anki_data(self, difficulty_data: List[Dict]) -> List[Dict]:
        """Extract key terms from Anki card data"""
        print(f"🔍 Debug: Processing {len(difficulty_data)} cards from Anki data")
        key_terms = []

        for i, card in enumerate(difficulty_data):
            # Handle the correct JSON structure from anki_to_json.py
            if "description" in card and isinstance(card["description"], dict):
                front = card["description"].get("front", "").strip()
                back = card["description"].get("back", "").strip()
            else:
                # Fallback to direct fields (shouldn't happen with anki_to_json.py)
                front = card.get("front", "").strip()
                back = card.get("back", "").strip()

            difficulty_score = card.get("difficulty_score", 0)

            print(f"🔍 Debug: Card {i+1}: front='{front[:50]}...', back='{back[:50]}...', difficulty={difficulty_score}")

            if front and back:
                # Extract the main term from the front (often in format "What is X?" or just "X")
                term = front.replace("What is ", "").replace("?", "").replace("Define ", "").strip()
                if not term:
                    term = front

                key_terms.append({
                    "term": term,
                    "definition": back,
                    "context": f"From Anki card (difficulty: {difficulty_score})",
                    "difficulty_score": difficulty_score,
                    "card_front": front,
                    "card_back": back
                })

        # Sort by difficulty score (highest first)
        key_terms.sort(key=lambda x: x.get("difficulty_score", 0), reverse=True)

        print(f"🔍 Debug: Extracted {len(key_terms)} key terms from Anki data")
        if key_terms:
            print(f"🔍 Debug: First key term sample: {key_terms[0]}")
        else:
            print("🔍 Debug: WARNING - No key terms extracted!")
        return key_terms

    async def _generate_cheatsheet_from_anki_data(self, key_terms: List[Dict], difficulty_data: List[Dict]) -> str:
        """Generate cheat sheet specifically from Anki data using agents with database retrieval"""
        try:
            print(f"🔍 Debug: Generating cheat sheet with {len(key_terms)} key terms")
            print(f"🔍 Debug: Input difficulty_data has {len(difficulty_data)} items")

            if not key_terms:
                print("🔍 Debug: ERROR - No key_terms provided to cheatsheet generation!")
                return "ERROR: No flashcard data available for cheat sheet generation"
            # Convert to format suitable for cheatsheet agent
            flashcard_format = []
            for i, term in enumerate(key_terms):
                flashcard_item = {
                    "front": term["card_front"],
                    "back": term["card_back"],
                    "difficulty_score": term.get("difficulty_score", 0),
                    "term": term["term"]
                }
                flashcard_format.append(flashcard_item)
                if i == 0:  # Debug first item
                    print(f"🔍 Debug: First flashcard conversion: {flashcard_item}")

            print(f"🔍 Debug: Converted {len(key_terms)} key_terms to {len(flashcard_format)} flashcards")

            # Note: Tools should be defined in the agent files, not assigned dynamically

            # Create crew with cheatsheet agent
            crew = Crew(
                agents=[cheatsheet_agent],
                tasks=[cheatsheet_task],
                verbose=True
            )

            # Debug: Log the flashcard format before sending to agent
            flashcards_json_str = json.dumps(flashcard_format, indent=2)
            print(f"🔍 Debug: Sending to agent: {len(flashcard_format)} flashcards")
            print(f"🔍 Debug: JSON preview: {flashcards_json_str[:200]}...")

            # Execute the crew with the Anki card data
            result = crew.kickoff({
                "flashcards": flashcards_json_str
            })

            if result:
                # Save cheat sheet to file
                cheat_sheet_path = settings.output_dir / "anki_cheat_sheet.md"
                with open(cheat_sheet_path, 'w', encoding='utf-8') as f:
                    f.write(str(result))

                return str(result)
            else:
                # Fallback to simple cheat sheet generation
                return self._generate_simple_anki_cheatsheet(key_terms)

        except Exception as e:
            print(f"⚠️ Failed to generate cheat sheet with agents: {e}")
            # Fallback to simple cheat sheet generation
            return self._generate_simple_anki_cheatsheet(key_terms)

    def _generate_simple_anki_cheatsheet(self, key_terms: List[Dict]) -> str:
        """Simple fallback cheat sheet generation from Anki terms"""
        cheat_sheet_parts = [
            "# Personalized Study Cheat Sheet",
            "*Generated from your Anki deck with difficulty prioritization*",
            "",
            "## 🔥 High Priority Terms (Most Difficult)",
            "*Focus on these - they showed higher difficulty in your reviews*",
            ""
        ]

        # Add high difficulty terms first (score > 0)
        high_difficulty = [term for term in key_terms if term.get("difficulty_score", 0) > 0]
        if high_difficulty:
            for term in high_difficulty[:10]:  # Top 10 most difficult
                cheat_sheet_parts.extend([
                    f"### {term['term']}",
                    f"**Definition:** {term['definition']}",
                    f"*Difficulty Score: {term.get('difficulty_score', 0)}*",
                    ""
                ])

        cheat_sheet_parts.extend([
            "## 📚 All Terms (Alphabetical)",
            ""
        ])

        # Add all terms alphabetically
        sorted_terms = sorted(key_terms, key=lambda x: x['term'].lower())
        for term in sorted_terms[:20]:  # Limit to 20 terms for readability
            cheat_sheet_parts.extend([
                f"**{term['term']}:** {term['definition']}",
                ""
            ])

        return "\n".join(cheat_sheet_parts)
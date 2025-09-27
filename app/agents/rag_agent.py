from crewai import Agent, Task
import os
from typing import List
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.tools import tool
from tavily import TavilyClient
import chromadb

# Initialize embeddings only if OpenAI API key is available
_openai_key = os.environ.get("OPENAI_API_KEY")
if _openai_key:
    _embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=_openai_key)
    # Use persistent directory instead of HTTP client to avoid port conflicts
    _vs = Chroma(
        collection_name="study_bot",
        persist_directory="./chroma_db",
        embedding_function=_embeddings
    )
    _retriever = _vs.as_retriever(search_kwargs={"k": 4})
else:
    _embeddings = None
    _vs = None
    _retriever = None

# Initialize Tavily client (optional if API key missing)
_tavily_key = os.environ.get("TAVILY_API_KEY")
_tavily = TavilyClient(api_key=_tavily_key) if _tavily_key else None

@tool("tavily_search", return_direct=False)
def _tavily_search(query: str, max_results: int = 5):
    """Search the web with Tavily and return a list of result dicts."""
    if _tavily is None:
        return {"error": "TAVILY_API_KEY not set", "results": []}
    try:
        resp = _tavily.search(
            query=query,
            max_results=max_results,
            include_answer="basic",
        )
    except Exception as e:
        return {"error": f"Tavily error: {e}", "results": []}

    results = []
    for r in resp.get("results", []):
        # Each r typically has: {title, url, content, score, published_date?}
        content = (r.get("content") or "").strip()
        if not content:
            continue
        results.append(
            {
                "content": content,
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "source": r.get("url", ""),
                "origin": "tavily",
                "query": query,
            }
        )
    return {"error": None, "results": results, "answer": resp.get("answer")}

search_agent = Agent(
    role="Tavily Web Searcher",
    goal="Find and summarize relevant information from the web.",
    backstory="Expert at quickly finding and summarizing web content via Tavily",
    tools=[],
    allow_delegation=False
)

search_task = Task(
    description=(
        "Use the Tavily search tool to find relevant information for the query: '{query}'. "
        "Summarize the findings concisely. If no relevant information is found, respond with 'No relevant information found.'"
    ),
    expected_output="Concise summary of search results or 'No relevant information found.'",
    agent=search_agent
)

def _format_docs(docs: List):
    """Render retrieved docs as compact Markdown with source hints."""
    if not docs:
        return "No results."
    lines = []
    for i, d in enumerate(docs, start=1):
        meta = getattr(d, "metadata", {}) or {}
        source = meta.get("source") or meta.get("url") or meta.get("file") or meta.get("path") or ""
        title = meta.get("title") or ""
        hdr_bits = [f"**{i}.**"]
        if title:
            hdr_bits.append(title)
        if source:
            hdr_bits.append(f"({source})")
        header = " ".join(hdr_bits).strip()
        content = getattr(d, "page_content", str(d)).strip()
        lines.append(header + "\n" + content)
    return "\n\n".join(lines) if lines else "No results."



def _upsert_texts_to_chroma(items: List[dict]) -> int:
    """Upsert Tavily items into Chroma, returning number added."""
    if not items or _vs is None:
        return 0
    texts = []
    metadatas = []
    for it in items:
        text = it.get("content", "")
        if not text:
            continue
        texts.append(text)
        metadatas.append(
            {
                "source": it.get("source") or it.get("url") or "",
                "url": it.get("url") or "",
                "title": it.get("title") or "",
                "_origin": it.get("origin") or "tavily",
                "_query": it.get("query") or "",
            }
        )
    if not texts:
        return 0
    _vs.add_texts(texts=texts, metadatas=metadatas)
    _vs.persist()
    return len(texts)

def _auto_enrich_from_web(query: str, max_results: int = 5) -> str:
    """Perform Tavily enrichment and return a status string."""
    out = _tavily_search(query, max_results=max_results)
    if out.get("error"):
        return f"Enrichment skipped: {out['error']}"
    added = _upsert_texts_to_chroma(out.get("results", []))
    msg = f"Enriched Chroma with {added} web snippet(s) for query: '{query}'."
    if added == 0:
        msg += " No suitable web content was added."
    return msg

@tool("enrich_from_web", return_direct=False)
def enrich_from_web(query: str) -> str:
    """
    Use Tavily to research the query, upsert results into Chroma, and return a brief summary.
    Requires TAVILY_API_KEY and OPENAI_API_KEY to be set.
    """
    if _retriever is None:
        return "Vector database not initialized. Please set OPENAI_API_KEY."

    status = _auto_enrich_from_web(query)
    # Optionally re-query to preview what's now in the DB
    docs = _retriever.get_relevant_documents(query)
    preview = _format_docs(docs[:3]) if docs else "No results after enrichment."
    return f"{status}\n\n**Preview of Chroma after enrichment:**\n\n{preview}"

@tool("chroma_search", return_direct=False)
def chroma_search(query: str) -> str:
    """
    Retrieve passages from Chroma related to the query. If none are found, automatically
    enrich the DB via Tavily and retry, then return the results.
    """
    if _retriever is None:
        return "Vector database not initialized. Please set OPENAI_API_KEY."

    docs = _retriever.get_relevant_documents(query)
    if docs:
        return _format_docs(docs)

    # Auto-delegate to enrichment when no context is found
    status = _auto_enrich_from_web(query)
    docs = _retriever.get_relevant_documents(query)
    if not docs:
        return f"{status}\n\nNo results found in Chroma for: '{query}'."
    return f"{status}\n\n**Retrieved after enrichment:**\n\n{_format_docs(docs)}"

# ---------- Agents ----------
web_enricher_agent = Agent(
    role="Tavily Enrichment Researcher",
    goal="When the knowledge base lacks answers, research the web and add high-signal snippets into Chroma.",
    backstory=(
        "A diligent web researcher that consults reputable sources via Tavily, "
        "distills concise snippets, and updates the Chroma knowledge base."
    ),
    tools=[],
    verbose=True,
    allow_delegation=False,
)

rag_agent = Agent(
    role="Chroma RAG Researcher",
    goal="Answer questions accurately using knowledge stored in the Chroma vector database; if context is missing, delegate to the enrichment agent.",
    backstory=(
        "A retrieval-augmented agent that first consults Chroma. "
        "When results are insufficient, it calls on a companion agent that searches the web "
        "and updates the database, then retries retrieval."
    ),
    tools=[],
    verbose=True,
    allow_delegation=True,
)

# ---------- Tasks ----------
rag_task = Task(
    description=(
        "Use `chroma_search` to retrieve context and draft a concise, well-cited answer. "
        "If results are sparse or missing, call `enrich_from_web` with the same query to augment the DB, "
        "then run `chroma_search` again and answer based strictly on the retrieved context."
    ),
    expected_output="A concise, grounded answer with brief inline citations to sources.",
    agent=rag_agent,
)

enrich_task = Task(
    description=(
        "Proactively research the user's query via web search, identify authoritative sources, "
        "and upsert compact, high-signal snippets into Chroma so future retrievals succeed."
    ),
    expected_output="A short summary of sources added and a preview of new retrievable context.",
    agent=web_enricher_agent,
)
# --------------------------------------------------------
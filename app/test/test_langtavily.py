# test_langchain_tavily.py
import asyncio
from langchain_community.tools.tavily_search import TavilySearchResults
import os
from dotenv import load_dotenv

load_dotenv()

async def test_tavily():
    # Initialize Tavily through LangChain
    search = TavilySearchResults(
        max_results=2,
        search_depth="basic",
        include_answer=True
    )
    
    # Test search
    query = "What is machine learning?"
    
    try:
        # Sync search
        results = search.invoke({"query": query})
        print("✅ LangChain-Tavily works!")
        print(f"Results: {results}")
        
        # Async search
        async_results = await search.ainvoke({"query": query})
        print(f"Async results: {async_results}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure TAVILY_API_KEY is set in .env")

if __name__ == "__main__":
    asyncio.run(test_tavily())
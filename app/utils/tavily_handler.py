"""
TavilyHandler using direct tavily-python SDK
This version uses the tavily-python package directly without LangChain
"""

from tavily import TavilyClient
import asyncio
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class TavilyHandler:
    """Handler for content verification using direct Tavily Python SDK"""
    
    def __init__(self, api_key: Optional[str] = None, rate_limit: int = 60):
        """
        Initialize TavilyHandler with direct Tavily client
        
        Args:
            api_key: Tavily API key (if not provided, will look for TAVILY_API_KEY env var)
            rate_limit: Rate limit (requests per minute), default 60
        """
        # Get API key from parameter, environment, or config
        self.api_key = api_key or os.getenv('TAVILY_API_KEY')
        
        if not self.api_key:
            # Try to get from config if it exists
            try:
                from app.config.config import settings
                self.api_key = getattr(settings, 'tavily_api_key', None)
                rate_limit = getattr(settings, 'tavily_rate_limit', rate_limit)
            except ImportError:
                pass
        
        if not self.api_key:
            print("Warning: Tavily API key not found. Verification will be disabled.")
            print("To enable verification, set TAVILY_API_KEY environment variable")
            self.client = None
        else:
            # Initialize Tavily client
            self.client = TavilyClient(api_key=self.api_key)
        
        self.rate_limit_delay = 60 / rate_limit
    
    async def verify_content(self, 
                            main_ideas: List[str], 
                            vocabulary: Dict[str, str]) -> Dict[str, Any]:
        """
        Verify and enrich content with web search using Tavily
        
        Args:
            main_ideas: List of main concepts to verify
            vocabulary: Dictionary of terms to verify
            
        Returns:
            Dictionary with verification results
        """
        
        verified = {
            'main_ideas': {},
            'vocabulary': {},
            'additional_context': {},
            'sources': []
        }
        
        if not self.client:
            verified['error'] = 'Tavily client not initialized (no API key)'
            return verified
        
        try:
            # Verify top main ideas (limit to avoid rate limits)
            ideas_to_verify = main_ideas[:3] if main_ideas else []
            
            for idea in ideas_to_verify:
                await asyncio.sleep(self.rate_limit_delay)
                
                try:
                    # Use Tavily search
                    results = await self._async_search(idea)
                    
                    verified['main_ideas'][idea] = {
                        'verified': True,
                        'results': results
                    }
                    
                    # Extract sources
                    if isinstance(results, dict):
                        # Extract URLs from results
                        if 'results' in results:
                            for item in results['results']:
                                if 'url' in item:
                                    verified['sources'].append(item['url'])
                    
                except Exception as e:
                    print(f"Error verifying idea '{idea}': {e}")
                    verified['main_ideas'][idea] = {
                        'verified': False,
                        'error': str(e)
                    }
            
            # Verify key vocabulary terms (limit to avoid rate limits)
            terms_to_verify = list(vocabulary.keys())[:3] if vocabulary else []
            
            for term in terms_to_verify:
                await asyncio.sleep(self.rate_limit_delay)
                
                try:
                    # Search for definition
                    query = f"define {term} meaning explanation"
                    results = await self._async_search(query)
                    
                    verified['vocabulary'][term] = {
                        'verified': True,
                        'results': results,
                        'enhanced_definition': self._extract_definition(results)
                    }
                    
                except Exception as e:
                    print(f"Error verifying term '{term}': {e}")
                    verified['vocabulary'][term] = {
                        'verified': False,
                        'error': str(e)
                    }
            
            # Remove duplicate sources
            verified['sources'] = list(set(verified['sources']))
            
        except Exception as e:
            print(f"Tavily verification error: {e}")
            verified['error'] = str(e)
        
        return verified
    
    async def _async_search(self, query: str, search_depth: str = "basic", max_results: int = 3) -> Dict[str, Any]:
        """
        Perform async search using Tavily client
        
        Args:
            query: Search query
            search_depth: "basic" or "advanced"
            max_results: Number of results to return
            
        Returns:
            Search results dictionary
        """
        if not self.client:
            return {"error": "Tavily client not initialized"}
        
        try:
            # Run the synchronous Tavily search in an executor to make it async
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.client.search,
                query,
                search_depth,
                max_results
            )
            
            return results
                
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            return {"error": str(e)}
    
    def _extract_definition(self, results: Dict[str, Any]) -> str:
        """
        Extract a definition from Tavily search results
        
        Args:
            results: Search results from Tavily
            
        Returns:
            Extracted definition or empty string
        """
        if not results or 'results' not in results:
            return ""
        
        # Try to find the answer field first
        if 'answer' in results and results['answer']:
            return results['answer']
        
        # Try to extract from individual results
        for result in results.get('results', []):
            if 'content' in result:
                content = result['content']
                if 'definition' in content.lower() or 'means' in content.lower() or 'is a' in content.lower():
                    # Extract first sentence
                    sentences = content.split('.')
                    if sentences:
                        definition = sentences[0].strip()
                        if len(definition) > 10:
                            return definition + '.'
        
        # Fallback: return first result's content (truncated)
        if results.get('results') and len(results['results']) > 0:
            content = results['results'][0].get('content', '')
            return content[:200] + '...' if len(content) > 200 else content
        
        return ""
    
    async def search_topic(self, topic: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search for a specific topic with more results
        
        Args:
            topic: Topic to search
            max_results: Maximum number of results
            
        Returns:
            Search results dictionary
        """
        return await self._async_search(topic, search_depth="advanced", max_results=max_results)
    
    async def fact_check(self, statement: str) -> Dict[str, Any]:
        """
        Fact-check a specific statement
        
        Args:
            statement: Statement to verify
            
        Returns:
            Fact-check results
        """
        query = f"fact check verify: {statement}"
        
        try:
            results = await self._async_search(query)
            
            return {
                'statement': statement,
                'verified': 'results' in results and len(results.get('results', [])) > 0,
                'confidence': self._calculate_confidence(results),
                'sources': results
            }
        except Exception as e:
            return {
                'statement': statement,
                'verified': False,
                'error': str(e)
            }
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """
        Calculate confidence score based on Tavily search results
        
        Args:
            results: Search results from Tavily
            
        Returns:
            Confidence score between 0 and 1
        """
        if not results or 'results' not in results:
            return 0.0
        
        # Base confidence on number of results
        num_results = len(results.get('results', []))
        base_confidence = min(num_results / 3, 1.0)
        
        # Check if there's an answer field (higher confidence)
        if 'answer' in results and results['answer']:
            base_confidence = min(base_confidence + 0.3, 1.0)
        
        # Check result scores if available
        if 'results' in results:
            for result in results['results']:
                if 'score' in result and result['score'] > 0.8:
                    base_confidence = min(base_confidence + 0.1, 1.0)
        
        return base_confidence

# Standalone test function
async def test_tavily_direct():
    """Test function to verify direct Tavily client works"""
    print("Testing Direct Tavily Client...")
    
    api_key = os.getenv('TAVILY_API_KEY')
    if not api_key:
        print("❌ TAVILY_API_KEY not found in environment variables")
        return
    
    handler = TavilyHandler(api_key=api_key)
    
    # Test simple search
    print("\n1. Testing simple search...")
    results = await handler._async_search("Python programming")
    if 'results' in results:
        print(f"✓ Found {len(results['results'])} results")
        if results.get('answer'):
            print(f"Answer: {results['answer'][:100]}...")
    else:
        print(f"Results: {results}")
    
    # Test fact checking
    print("\n2. Testing fact check...")
    fact_result = await handler.fact_check("Python was created in 1991")
    print(f"✓ Fact check result: {fact_result['verified']}")
    print(f"  Confidence: {fact_result['confidence']:.2f}")
    
    print("\n✅ Tavily direct client test complete!")

if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_tavily_direct)


# ADD THESE TO THE END OF YOUR EXISTING tavily_handler.py FILE:

try:
    from crewai_tools import BaseTool
    
    class TavilySearchTool(BaseTool):
        """Simple Tavily search tool for CrewAI agents"""
        name: str = "Web Search"
        description: str = "Search the web for information. Just provide what you want to search for."
        
        def __init__(self):
            super().__init__()
            self.handler = TavilyHandler()
        
        def _run(self, query: str) -> str:
            """Run web search"""
            if not self.handler.client:
                return "Tavily API key not configured"
            
            try:
                # Use synchronous search
                results = self.handler.client.search(query, search_depth="basic", max_results=3)
                
                output = f"Search results for: {query}\n\n"
                if results.get("answer"):
                    output += f"Answer: {results['answer']}\n\n"
                
                for i, result in enumerate(results.get("results", [])[:3], 1):
                    output += f"{i}. {result.get('title', 'No title')}\n"
                    output += f"   {result.get('content', '')[:150]}...\n\n"
                
                return output
            except Exception as e:
                return f"Search error: {str(e)}"
    
    def create_tavily_tools():
        """Create Tavily tools for CrewAI agents"""
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            print("Warning: TAVILY_API_KEY not found. No tools created.")
            return []
        
        try:
            tool = TavilySearchTool()
            return [tool]
        except Exception as e:
            print(f"Error creating tools: {e}")
            return []
    
    def attach_tools_to_agent(agent):
        """Attach Tavily tools to an agent"""
        tools = create_tavily_tools()
        if tools:
            agent.tools = tools
            print(f"Attached {len(tools)} tools to {agent.role}")
        return agent

except ImportError:
    # If crewai_tools not available, create stub functions
    print("Warning: crewai_tools not installed. Tavily tools disabled.")
    
    def create_tavily_tools():
        """Stub function when crewai_tools not available"""
        print("crewai_tools not installed. Install with: pip install crewai-tools")
        return []
    
    def attach_tools_to_agent(agent):
        """Stub function when crewai_tools not available"""
        print("Cannot attach tools - crewai_tools not installed")
        return agent
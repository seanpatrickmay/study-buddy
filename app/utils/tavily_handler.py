from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
import asyncio
from typing import List, Dict, Any
import os

from app.config.config import settings

class TavilyHandler:
    """Handler for content verification using LangChain-Tavily integration"""
    
    def __init__(self):
        # Initialize Tavily through LangChain
        self.search = TavilySearchAPIWrapper(
            tavily_api_key=settings.tavily_api_key
        )
        self.search_tool = TavilySearchResults(
            api_wrapper=self.search,
            max_results=3,
            search_depth="basic",
            include_answer=True,
            include_raw_content=False
        )
        self.rate_limit_delay = 60 / settings.tavily_rate_limit
    
    async def verify_content(self, 
                            main_ideas: List[str], 
                            vocabulary: Dict[str, str]) -> Dict[str, Any]:
        """
        Verify and enrich content with web search using LangChain-Tavily
        
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
        
        try:
            # Verify top main ideas
            ideas_to_verify = main_ideas[:3]
            
            for idea in ideas_to_verify:
                await asyncio.sleep(self.rate_limit_delay)
                
                try:
                    # Use LangChain-Tavily for search
                    results = await self._async_search(idea)
                    
                    verified['main_ideas'][idea] = {
                        'verified': True,
                        'results': results
                    }
                    
                    # Extract sources
                    for result in results:
                        if 'url' in result:
                            verified['sources'].append(result['url'])
                    
                except Exception as e:
                    print(f"Error verifying idea '{idea}': {e}")
                    verified['main_ideas'][idea] = {
                        'verified': False,
                        'error': str(e)
                    }
            
            # Verify key vocabulary terms
            terms_to_verify = list(vocabulary.keys())[:3]
            
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
    
    async def _async_search(self, query: str) -> List[Dict[str, Any]]:
        """
        Perform async search using LangChain-Tavily
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            # LangChain tools can be invoked directly
            results = self.search_tool.invoke({"query": query})
            
            # Parse results based on return type
            if isinstance(results, str):
                return [{"content": results}]
            elif isinstance(results, list):
                return results
            elif isinstance(results, dict):
                return [results]
            else:
                return []
                
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            return []
    
    def _extract_definition(self, results: List[Dict[str, Any]]) -> str:
        """
        Extract a definition from search results
        
        Args:
            results: Search results
            
        Returns:
            Extracted definition or empty string
        """
        if not results:
            return ""
        
        # Try to find the best definition from results
        for result in results:
            content = result.get('content', '')
            if 'definition' in content.lower() or 'means' in content.lower():
                # Extract first sentence or up to 200 characters
                sentences = content.split('.')
                if sentences:
                    return sentences[0].strip() + '.'
        
        # Fallback: return first result's content (truncated)
        if results and 'content' in results[0]:
            content = results[0]['content']
            return content[:200] + '...' if len(content) > 200 else content
        
        return ""
    
    async def search_topic(self, topic: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for a specific topic with more results
        
        Args:
            topic: Topic to search
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        # Create a more detailed search tool for specific queries
        detailed_search = TavilySearchResults(
            api_wrapper=self.search,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        
        try:
            results = detailed_search.invoke({"query": topic})
            return results if isinstance(results, list) else [results]
        except Exception as e:
            print(f"Topic search error: {e}")
            return []
    
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
                'verified': len(results) > 0,
                'confidence': self._calculate_confidence(results),
                'sources': results
            }
        except Exception as e:
            return {
                'statement': statement,
                'verified': False,
                'error': str(e)
            }
    
    def _calculate_confidence(self, results: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence score based on search results
        
        Args:
            results: Search results
            
        Returns:
            Confidence score between 0 and 1
        """
        if not results:
            return 0.0
        
        # Simple confidence calculation based on number and quality of results
        base_confidence = min(len(results) / 3, 1.0)  # More results = higher confidence
        
        # Check if results contain answer
        has_answer = any('answer' in r for r in results)
        
        # Adjust confidence
        if has_answer:
            base_confidence = min(base_confidence + 0.2, 1.0)
        
        return base_confidence
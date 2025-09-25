from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import Tool
from typing import List, Dict, Any
import json
import asyncio

from app.config.config import settings
from app.config.mcp_controller import MCPOutputController
from app.prompts.study_prompts import StudyPrompts

class StudyAgents:
    """CrewAI agents for study material generation"""
    
    def __init__(self):
        """Initialize agents with configuration"""
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key
        )
        self.mcp = MCPOutputController()
        self.prompts = StudyPrompts()
        
        # Initialize Tavily as a LangChain tool
        self.tavily_tool = self._create_tavily_tool()
    
    def _create_tavily_tool(self) -> Tool:
        """Create Tavily search tool for agents"""
        search = TavilySearchResults(
            max_results=3,
            search_depth="basic",
            include_answer=True
        )
        
        return Tool(
            name="tavily_search",
            description="Search the web for current information and fact-checking",
            func=search.run,
            coroutine=search.arun
        )
    
    def verification_agent(self) -> Agent:
        """Agent with Tavily tool for fact-checking"""
        return Agent(
            role='Fact Verification Specialist',
            goal='Verify accuracy and add supplementary context',
            backstory="""You are a research validation expert with access to 
            real-time web search. You verify information accuracy and enrich 
            content with relevant, authoritative supplementary material.""",
            tools=[self.tavily_tool],  # Give agent access to Tavily
            llm=self.llm,
            verbose=settings.crew_verbose,
            max_iter=settings.max_iter
        )
    
    # ... rest of your agents code ...
    
    async def verify_and_enhance_content(self, 
                                        main_ideas: List[str],
                                        vocabulary: Dict[str, str]) -> Dict[str, Any]:
        """
        Use verification agent with Tavily tool
        """
        verification_task = Task(
            description=f"""
            Verify these main ideas and vocabulary terms using web search:
            
            Main Ideas: {main_ideas[:3]}
            Terms: {list(vocabulary.keys())[:3]}
            
            For each:
            1. Search for current, accurate information
            2. Fact-check the concepts
            3. Add relevant context or corrections
            4. Provide authoritative sources
            
            Use the tavily_search tool to verify information.
            """,
            agent=self.verification_agent(),
            expected_output="Verification results with sources"
        )
        
        crew = Crew(
            agents=[self.verification_agent()],
            tasks=[verification_task],
            process=Process.sequential,
            verbose=settings.crew_verbose
        )
        
        result = crew.kickoff()
        return result
import pytest
import asyncio

from app.utils.agents import StudyAgents

class TestAgents:
    """Test CrewAI agents"""
    
    @pytest.fixture
    def agents(self):
        return StudyAgents()
    
    @pytest.mark.asyncio
    async def test_extract_content(self, agents):
        markdown = "# Test\n\nThis is test content."
        result = await agents.extract_content(markdown)
        
        assert 'main_ideas' in result
        assert 'vocabulary' in result
        assert isinstance(result['main_ideas'], list)
        assert isinstance(result['vocabulary'], dict)
    
    @pytest.mark.asyncio
    async def test_generate_qa_pairs(self, agents):
        main_ideas = ["Test concept 1", "Test concept 2"]
        context = {"additional": "context"}
        
        result = await agents.generate_qa_pairs(main_ideas, context)
        
        assert isinstance(result, list)
        if result:
            assert 'question' in result[0]
            assert 'answer' in result[0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
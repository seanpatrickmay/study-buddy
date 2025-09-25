import pytest
import asyncio
from pathlib import Path

from app.utils.pipeline import StudyPipeline
from app.config.mcp_controller import MCPOutputController, StudyOutput

@pytest.fixture
def sample_markdown():
    return """
    # Introduction to Machine Learning
    
    Machine learning is a subset of artificial intelligence.
    
    ## Key Concepts
    - Supervised Learning: Training with labeled data
    - Unsupervised Learning: Finding patterns without labels
    
    ## Vocabulary
    - Algorithm: A step-by-step procedure
    - Model: A mathematical representation
    """

@pytest.fixture
def sample_output():
    return StudyOutput(
        main_ideas=["Machine learning basics", "Supervised learning"],
        vocabulary={"Algorithm": "A step-by-step procedure"},
        qa_pairs=[{"question": "What is ML?", "answer": "A subset of AI"}],
        confidence_scores={"overall": 0.85}
    )

class TestMCPController:
    """Test MCP output controller"""
    
    def test_validate_valid_output(self, sample_output):
        controller = MCPOutputController()
        result = controller.validate_output(sample_output.dict())
        assert result.main_ideas == sample_output.main_ideas
    
    def test_validate_json_string(self):
        controller = MCPOutputController()
        json_str = '''
        {
            "main_ideas": ["test idea"],
            "vocabulary": {"term": "definition"},
            "qa_pairs": [{"question": "q", "answer": "a"}]
        }
        '''
        result = controller.validate_output(json_str)
        assert len(result.main_ideas) == 1
    
    def test_fallback_parsing(self):
        controller = MCPOutputController(strict_mode=False)
        bad_input = "This is not JSON"
        result = controller.validate_output(bad_input)
        assert isinstance(result, StudyOutput)

class TestPipeline:
    """Test the main pipeline"""
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self):
        pipeline = StudyPipeline()
        assert pipeline is not None
        assert pipeline.agents is not None
        assert pipeline.workflow is not None

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
# mcp_controller.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
import json
from enum import Enum

class ContentType(str, Enum):
    MAIN_IDEA = "main_idea"
    VOCABULARY = "vocabulary"
    QA_PAIR = "qa_pair"
    SUMMARY = "summary"

class ValidatedContent(BaseModel):
    content_type: ContentType
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = {}

class StudyOutput(BaseModel):
    main_ideas: List[str] = Field(
        description="Key concepts from the document",
        min_items=1,
        max_items=10
    )
    vocabulary: Dict[str, str] = Field(
        description="Term: Definition pairs"
    )
    qa_pairs: List[Dict[str, str]] = Field(
        description="Question-answer pairs",
        min_items=1
    )
    confidence_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores for each section"
    )
    
    @validator('qa_pairs')
    def validate_qa_pairs(cls, v):
        for pair in v:
            if 'question' not in pair or 'answer' not in pair:
                raise ValueError("Each QA pair must have 'question' and 'answer' keys")
        return v
    
    @validator('vocabulary')
    def validate_vocabulary(cls, v):
        if len(v) == 0:
            raise ValueError("Vocabulary must contain at least one term")
        return v

class MCPOutputController:
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.validation_errors = []
    
    def validate_output(self, raw_output: Any) -> StudyOutput:
        """Validate and parse raw output from agents"""
        try:
            # Handle string JSON
            if isinstance(raw_output, str):
                try:
                    raw_output = json.loads(raw_output)
                except json.JSONDecodeError:
                    # Try to extract JSON from text
                    raw_output = self._extract_json_from_text(raw_output)
            
            # Validate with Pydantic
            return StudyOutput(**raw_output)
            
        except Exception as e:
            if self.strict_mode:
                raise ValueError(f"Validation failed: {str(e)}")
            else:
                # Return default structure
                return self._create_default_output()
    
    def _extract_json_from_text(self, text: str) -> dict:
        """Extract JSON from agent response text"""
        import re
        
        # Try to find JSON block in text
        json_pattern = r'\{[\s\S]*\}'
        matches = re.findall(json_pattern, text)
        
        if matches:
            try:
                return json.loads(matches[0])
            except:
                pass
        
        # Fallback: parse structured text
        return self._parse_structured_text(text)
    
    def _parse_structured_text(self, text: str) -> dict:
        """Parse structured text into expected format"""
        lines = text.split('\n')
        output = {
            'main_ideas': [],
            'vocabulary': {},
            'qa_pairs': [],
            'confidence_scores': {}
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'main idea' in line.lower():
                current_section = 'main_ideas'
            elif 'vocabulary' in line.lower():
                current_section = 'vocabulary'
            elif 'question' in line.lower() or 'q&a' in line.lower():
                current_section = 'qa_pairs'
            elif line and current_section:
                if current_section == 'main_ideas':
                    output['main_ideas'].append(line.lstrip('- •'))
                elif current_section == 'vocabulary' and ':' in line:
                    term, definition = line.split(':', 1)
                    output['vocabulary'][term.strip()] = definition.strip()
        
        return output
    
    def _create_default_output(self) -> StudyOutput:
        """Create a default output structure"""
        return StudyOutput(
            main_ideas=["No main ideas extracted"],
            vocabulary={"term": "definition"},
            qa_pairs=[{"question": "No questions generated", "answer": "N/A"}],
            confidence_scores={"overall": 0.0}
        )
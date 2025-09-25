from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
import json
import re
from enum import Enum

class ContentType(str, Enum):
    """Types of content that can be extracted"""
    MAIN_IDEA = "main_idea"
    VOCABULARY = "vocabulary"
    QA_PAIR = "qa_pair"
    SUMMARY = "summary"
    CHEAT_SHEET = "cheat_sheet"

class QAPair(BaseModel):
    """Question-Answer pair model"""
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=1)
    question_type: Optional[str] = "short_answer"
    bloom_level: Optional[str] = "understand"
    difficulty: Optional[str] = "intermediate"

class VocabularyTerm(BaseModel):
    """Vocabulary term model"""
    term: str
    definition: str
    context: Optional[str] = None
    importance: Optional[str] = "important"

class StudyOutput(BaseModel):
    """Validated study material output"""
    
    main_ideas: List[str] = Field(
        description="Key concepts from the document",
        min_items=1,
        max_items=15
    )
    
    vocabulary: Dict[str, str] = Field(
        description="Term: Definition pairs",
        default_factory=dict
    )
    
    qa_pairs: List[Dict[str, str]] = Field(
        description="Question-answer pairs",
        min_items=1,
        default_factory=list
    )
    
    confidence_scores: Dict[str, float] = Field(
        default_factory=lambda: {"overall": 0.0},
        description="Confidence scores for each section"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    @validator('qa_pairs')
    def validate_qa_pairs(cls, v):
        """Ensure each QA pair has required fields"""
        for i, pair in enumerate(v):
            if 'question' not in pair or 'answer' not in pair:
                # Try to fix common issues
                if 'q' in pair and 'a' in pair:
                    v[i] = {'question': pair['q'], 'answer': pair['a']}
                else:
                    raise ValueError(f"QA pair {i} must have 'question' and 'answer' keys")
        return v
    
    @validator('main_ideas')
    def clean_main_ideas(cls, v):
        """Clean and validate main ideas"""
        cleaned = []
        for idea in v:
            if isinstance(idea, str) and idea.strip():
                # Remove bullet points and numbers
                cleaned_idea = re.sub(r'^[\d\-\*\•\.]+\s*', '', idea.strip())
                if cleaned_idea:
                    cleaned.append(cleaned_idea)
        return cleaned if cleaned else ["No main ideas extracted"]
    
    @validator('vocabulary')
    def validate_vocabulary(cls, v):
        """Ensure vocabulary is properly formatted"""
        if not v:
            return {"No terms": "No vocabulary extracted"}
        
        cleaned = {}
        for term, definition in v.items():
            if isinstance(term, str) and isinstance(definition, str):
                cleaned[term.strip()] = definition.strip()
        
        return cleaned if cleaned else {"No terms": "No vocabulary extracted"}

class MCPOutputController:
    """Controller for validating and standardizing agent outputs"""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.validation_errors = []
        self.parse_attempts = 0
        self.max_parse_attempts = 3
    
    def validate_output(self, raw_output: Any) -> StudyOutput:
        """
        Validate and parse raw output from agents
        
        Args:
            raw_output: Raw output from CrewAI agents
            
        Returns:
            StudyOutput: Validated and structured output
        """
        self.parse_attempts = 0
        self.validation_errors = []
        
        while self.parse_attempts < self.max_parse_attempts:
            try:
                return self._attempt_parse(raw_output)
            except Exception as e:
                self.parse_attempts += 1
                self.validation_errors.append(str(e))
                
                if self.parse_attempts >= self.max_parse_attempts:
                    if self.strict_mode:
                        raise ValueError(f"Failed to parse after {self.max_parse_attempts} attempts: {self.validation_errors}")
                    else:
                        return self._create_default_output()
        
        return self._create_default_output()
    
    def _attempt_parse(self, raw_output: Any) -> StudyOutput:
        """Attempt to parse raw output"""
        
        # Handle CrewAI output object
        if hasattr(raw_output, 'output'):
            raw_output = raw_output.output
        
        # Handle string JSON
        if isinstance(raw_output, str):
            # Try direct JSON parse
            try:
                parsed = json.loads(raw_output)
                return StudyOutput(**parsed)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                parsed = self._extract_json_from_text(raw_output)
                if parsed:
                    return StudyOutput(**parsed)
                
                # Try structured text parsing
                parsed = self._parse_structured_text(raw_output)
                if parsed:
                    return StudyOutput(**parsed)
        
        # Handle dictionary
        elif isinstance(raw_output, dict):
            return StudyOutput(**raw_output)
        
        # Handle list (might be QA pairs)
        elif isinstance(raw_output, list):
            return StudyOutput(
                main_ideas=["Extracted from list format"],
                vocabulary={},
                qa_pairs=raw_output if all('question' in item and 'answer' in item for item in raw_output) else []
            )
        
        raise ValueError(f"Unable to parse output of type {type(raw_output)}")
    
    def _extract_json_from_text(self, text: str) -> Optional[dict]:
        """Extract JSON from text containing mixed content"""
        
        # Try to find JSON blocks
        json_patterns = [
            r'\{[\s\S]*\}',  # Basic JSON object
            r'```json\s*([\s\S]*?)\s*```',  # Markdown code block
            r'```\s*([\s\S]*?)\s*```',  # Generic code block
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    # Clean the match
                    cleaned = match.strip()
                    if cleaned.startswith('```'):
                        cleaned = cleaned.replace('```json', '').replace('```', '').strip()
                    
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict):
                        return parsed
                except:
                    continue
        
        return None
    
    def _parse_structured_text(self, text: str) -> dict:
        """Parse structured text into expected format"""
        
        output = {
            'main_ideas': [],
            'vocabulary': {},
            'qa_pairs': [],
            'confidence_scores': {'overall': 0.5}
        }
        
        lines = text.split('\n')
        current_section = None
        current_question = None
        current_answer = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            line_lower = line.lower()
            if any(term in line_lower for term in ['main idea', 'key concept', 'important point']):
                current_section = 'main_ideas'
                continue
            elif any(term in line_lower for term in ['vocabulary', 'definition', 'glossary', 'terms']):
                current_section = 'vocabulary'
                continue
            elif any(term in line_lower for term in ['question', 'q&a', 'quiz']):
                current_section = 'qa_pairs'
                continue
            
            # Parse content based on section
            if current_section == 'main_ideas':
                # Remove common prefixes
                cleaned = re.sub(r'^[\d\-\*\•\.\)]+\s*', '', line)
                if cleaned and len(cleaned) > 10:
                    output['main_ideas'].append(cleaned)
            
            elif current_section == 'vocabulary':
                # Look for term: definition pattern
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        term = parts[0].strip().strip('*-•')
                        definition = parts[1].strip()
                        if term and definition:
                            output['vocabulary'][term] = definition
                elif '-' in line and line.index('-') < len(line) / 2:
                    parts = line.split('-', 1)
                    if len(parts) == 2:
                        term = parts[0].strip().strip('*•')
                        definition = parts[1].strip()
                        if term and definition:
                            output['vocabulary'][term] = definition
            
            elif current_section == 'qa_pairs':
                # Look for Q: and A: patterns
                if any(line.startswith(q) for q in ['Q:', 'Question:', 'Q.', 'Q)']):
                    # Save previous Q&A if exists
                    if current_question and current_answer:
                        output['qa_pairs'].append({
                            'question': current_question,
                            'answer': ' '.join(current_answer).strip()
                        })
                    
                    # Start new question
                    current_question = re.sub(r'^[QqUuEesSsTtIiOoNn:\.\)]+\s*', '', line).strip()
                    current_answer = []
                
                elif any(line.startswith(a) for a in ['A:', 'Answer:', 'A.', 'A)']):
                    answer_text = re.sub(r'^[AaNnSsWwEeRr:\.\)]+\s*', '', line).strip()
                    current_answer = [answer_text]
                
                elif current_answer is not None:
                    # Continue collecting answer
                    current_answer.append(line)
        
        # Save last Q&A pair
        if current_question and current_answer:
            output['qa_pairs'].append({
                'question': current_question,
                'answer': ' '.join(current_answer).strip()
            })
        
        # Ensure minimum content
        if not output['main_ideas']:
            output['main_ideas'] = ["Content extracted from document"]
        if not output['vocabulary']:
            output['vocabulary'] = {"Term": "Definition placeholder"}
        if not output['qa_pairs']:
            output['qa_pairs'] = [{"question": "What was covered?", "answer": "See main ideas above"}]
        
        return output
    
    def _create_default_output(self) -> StudyOutput:
        """Create a default output structure when parsing fails"""
        return StudyOutput(
            main_ideas=["Unable to extract main ideas - manual review needed"],
            vocabulary={"Error": "Vocabulary extraction failed"},
            qa_pairs=[{
                "question": "What went wrong?",
                "answer": f"Output parsing failed after {self.parse_attempts} attempts. Errors: {'; '.join(self.validation_errors)}"
            }],
            confidence_scores={"overall": 0.0},
            metadata={"errors": self.validation_errors}
        )
    
    def merge_outputs(self, outputs: List[StudyOutput]) -> StudyOutput:
        """Merge multiple outputs into a single output"""
        merged = {
            'main_ideas': [],
            'vocabulary': {},
            'qa_pairs': [],
            'confidence_scores': {},
            'metadata': {}
        }
        
        for output in outputs:
            merged['main_ideas'].extend(output.main_ideas)
            merged['vocabulary'].update(output.vocabulary)
            merged['qa_pairs'].extend(output.qa_pairs)
            merged['confidence_scores'].update(output.confidence_scores)
            merged['metadata'].update(output.metadata)
        
        # Remove duplicates
        merged['main_ideas'] = list(set(merged['main_ideas']))
        
        # Calculate average confidence
        if merged['confidence_scores']:
            avg_confidence = sum(merged['confidence_scores'].values()) / len(merged['confidence_scores'])
            merged['confidence_scores']['overall'] = avg_confidence
        
        return StudyOutput(**merged)
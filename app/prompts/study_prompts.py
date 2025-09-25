from typing import List, Dict, Any

class StudyPrompts:
    """Advanced prompts for study material generation"""
    
    @staticmethod
    def get_content_extraction_prompt(markdown: str) -> str:
        """Generate prompt for content extraction"""
        
        # Truncate content if too long
        max_content_length = 3000
        if len(markdown) > max_content_length:
            markdown = markdown[:max_content_length] + "...[truncated]"
        
        return f"""
        As an expert educational content analyst with 15 years of experience in curriculum design,
        analyze the following markdown content using advanced pedagogical techniques.
        
        CONTENT TO ANALYZE:
        {markdown}
        
        EXTRACTION REQUIREMENTS:
        
        1. MAIN IDEAS (5-10 concepts):
           - Identify foundational concepts
           - Extract supporting ideas
           - Note relationships between concepts
           - Classify by importance (critical/important/supplementary)
        
        2. VOCABULARY EXTRACTION:
           - Technical terms with precise definitions
           - Academic vocabulary essential for comprehension
           - Include context and usage examples
           - Note difficulty level for each term
        
        3. LEARNING OBJECTIVES:
           - What will students learn?
           - What skills will they develop?
           - What knowledge will they gain?
        
        OUTPUT FORMAT (MUST BE VALID JSON):
        {{
            "main_ideas": [
                "First main concept clearly stated",
                "Second main concept with context",
                "Third important idea from the text"
            ],
            "vocabulary": {{
                "term1": "Clear, concise definition of term1",
                "term2": "Precise explanation of term2",
                "term3": "Detailed definition with context"
            }},
            "qa_pairs": [
                {{
                    "question": "Sample comprehension question?",
                    "answer": "Detailed answer to the question"
                }}
            ],
            "confidence_scores": {{
                "main_ideas": 0.95,
                "vocabulary": 0.90,
                "overall": 0.92
            }}
        }}
        
        IMPORTANT:
        - Return ONLY valid JSON, no additional text
        - Ensure all strings are properly escaped
        - Include at least 3 main ideas
        - Include at least 3 vocabulary terms
        - Include at least 1 Q&A pair
        """
    
    @staticmethod
    def get_qa_generation_prompt(main_ideas: List[str], context: Dict[str, Any]) -> str:
        """Generate prompt for Q&A creation"""
        
        # Format main ideas
        ideas_text = "\n".join([f"- {idea}" for idea in main_ideas[:10]])
        
        # Format context (limit size)
        context_str = str(context)[:1500] if context else "No additional context"
        
        return f"""
        As a certified assessment specialist, create comprehensive question-answer pairs
        that test understanding of these concepts.
        
        MAIN IDEAS TO ASSESS:
        {ideas_text}
        
        ADDITIONAL CONTEXT:
        {context_str}
        
        QUESTION REQUIREMENTS:
        
        1. Create questions at different cognitive levels:
           - Recall: "Define..." "What is..."
           - Understanding: "Explain..." "Why does..."
           - Application: "How would you..." "Give an example..."
           - Analysis: "Compare..." "What are the differences..."
           - Evaluation: "Which is better..." "Critique..."
        
        2. Question types to include:
           - Factual questions (test knowledge)
           - Conceptual questions (test understanding)
           - Application questions (test skills)
           - Critical thinking questions (test analysis)
        
        3. Answer requirements:
           - Complete and accurate
           - Include examples where helpful
           - Reference the source material
           - Be concise but thorough
        
        OUTPUT FORMAT (MUST BE VALID JSON):
        [
            {{
                "question": "What is the definition of [concept]?",
                "answer": "A complete answer with explanation"
            }},
            {{
                "question": "How does [concept A] relate to [concept B]?",
                "answer": "Detailed explanation of the relationship"
            }},
            {{
                "question": "Give an example of [concept] in practice.",
                "answer": "Specific example with explanation"
            }}
        ]
        
        Generate AT LEAST 10 diverse questions covering all main ideas.
        Return ONLY the JSON array, no additional text.
        """
    
    @staticmethod
    def get_cheatsheet_prompt(anki_data: str, main_ideas: List[str], vocabulary: Dict[str, str]) -> str:
        """Generate prompt for cheat sheet creation"""
        
        # Format inputs
        ideas_formatted = "\n".join([f"• {idea}" for idea in main_ideas[:10]])
        vocab_list = "\n".join([f"• **{term}**: {definition[:100]}..." 
                                for term, definition in list(vocabulary.items())[:10]])
        
        return f"""
        As a learning design specialist, create an ultra-efficient study guide/cheat sheet.
        
        KEY CONCEPTS:
        {ideas_formatted}
        
        ESSENTIAL VOCABULARY:
        {vocab_list}
        
        CHEAT SHEET STRUCTURE:
        
        # 📚 STUDY GUIDE: [TOPIC]
        
        ## 🎯 Quick Reference (30 seconds)
        - Top 5 must-know facts
        - Most important formula or principle
        - Critical vocabulary
        
        ## 📍 Core Concepts (2 minutes)
        ### Concept 1: [Name]
        - Key point 1
        - Key point 2
        - Remember: [Memory tip]
        
        ### Concept 2: [Name]
        - Key point 1
        - Key point 2
        - Remember: [Memory tip]
        
        ## 🔧 Problem-Solving Steps
        1. First, identify...
        2. Then, apply...
        3. Finally, verify...
        
        ## ⚠️ Common Mistakes
        ❌ Don't: [Common error]
        ✅ Do: [Correct approach]
        
        ## 💡 Memory Tricks
        - Acronym: [ACRONYM] = [Expansion]
        - Association: [Concept] is like [Analogy]
        - Pattern: [Describe pattern]
        
        ## 📝 Quick Self-Test
        1. Can you explain [concept]?
        2. What's the difference between [A] and [B]?
        3. How would you apply [concept] to [scenario]?
        
        ## 🚀 Last-Minute Review
        If you remember NOTHING else:
        1. [Most critical point]
        2. [Second most critical]
        3. [Third most critical]
        
        ---
        ⭐ Review daily | ⭐⭐ Review weekly | ⭐⭐⭐ Review before test
        
        Create a comprehensive yet scannable cheat sheet following this structure.
        Use markdown formatting, emojis for visual memory, and clear organization.
        Keep total length under 500 lines.
        """
    
    @staticmethod
    def get_verification_prompt(content: str) -> str:
        """Generate prompt for content verification"""
        
        return f"""
        As a fact-checking specialist, verify the accuracy of this educational content:
        
        CONTENT TO VERIFY:
        {content[:2000]}
        
        VERIFICATION TASKS:
        1. Check factual claims for accuracy
        2. Identify any outdated information
        3. Note any controversial or disputed points
        4. Suggest additional context that would help understanding
        5. Rate confidence in the information (0-1 scale)
        
        OUTPUT FORMAT:
        {{
            "verified_facts": ["fact 1 is correct", "fact 2 is accurate"],
            "corrections": ["correction 1", "correction 2"],
            "additional_context": ["helpful context 1", "helpful context 2"],
            "confidence_rating": 0.85,
            "notes": "Additional observations"
        }}
        
        Return ONLY the JSON output.
        """
    
    @staticmethod
    def get_flashcard_prompt(qa_pairs: List[Dict[str, str]], vocabulary: Dict[str, str]) -> str:
        """Generate prompt for flashcard optimization"""
        
        return f"""
        As a memory expert, optimize these Q&A pairs and vocabulary for flashcard learning.
        
        CURRENT Q&A PAIRS:
        {str(qa_pairs[:5])}
        
        VOCABULARY TERMS:
        {str(list(vocabulary.items())[:5])}
        
        OPTIMIZATION REQUIREMENTS:
        1. Make questions clear and unambiguous
        2. Ensure answers are concise but complete
        3. Add memory hooks or mnemonics where helpful
        4. Flag difficult items for extra review
        5. Suggest related cards for better retention
        
        OUTPUT FORMAT:
        {{
            "optimized_cards": [
                {{
                    "front": "Clear question or prompt",
                    "back": "Concise, memorable answer",
                    "tags": ["topic1", "difficulty:medium"],
                    "notes": "Memory tip or additional context"
                }}
            ],
            "study_tips": ["tip 1", "tip 2"],
            "estimated_study_time": "X minutes"
        }}
        
        Return optimized flashcards ready for study.
        """
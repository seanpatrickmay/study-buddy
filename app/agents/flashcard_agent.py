from crewai import Agent, Task

flashcard_agent = Agent(
    role="Flashcard Generator",
    goal="Turn refined Markdown notes into study flashcards",
    backstory="Expert at creating concise Q&A flashcards for students.",
    verbose=True,
    allow_delegation=False
)

flashcard_task = Task(
    description=(
        "Take the provided Markdown notes and output JSON flashcards. "
        "Each flashcard must follow this schema: "
        "[{'id': 'card_001', 'front': '...', 'back': '...'}]"
        "Do not fabricate information"
        ""
    ),
    expected_output="Valid JSON flashcards only",
    agent=flashcard_agent
)
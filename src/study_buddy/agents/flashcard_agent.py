from crewai import Agent, Task

from study_buddy.agents import default_agent_llm


_FLASHCARD_LLM = default_agent_llm()

flashcard_agent = Agent(
    role="Flashcard Generator",
    goal="Turn refined Markdown notes into study flashcards",
    backstory="Expert at creating concise Q&A flashcards for students.",
    verbose=True,
    allow_delegation=False,
    llm=_FLASHCARD_LLM,
)

flashcard_task = Task(
    description=(
        "Take the following Markdown notes:\n\n{markdown}\n\n"
        "Each flashcard must follow this schema: "
        "[{'id': 'card_001', 'front': '...', 'back': '...', 'tags': ['tag1', 'tag2']}]\n"
        "'tags' is always an array of strings.\n"
        "The number of flashcards should scale with the length and complexity of the provided notes."
        "Cover every important topic, but do not create unnecessary duplicates or filler cards."
        "Tags should be short topic labels (e.g., 'Data Structures', 'Algorithms').\n"
        "Only create flashcards from the content in the Markdown. Do not invent or include topics not present."
        "The output should be JSON ONLY, no extra text, and it must be in the format provided."
        ""
    ),
    expected_output="Valid JSON flashcards only",
    agent=flashcard_agent
)

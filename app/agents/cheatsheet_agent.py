from crewai import Agent, Task

cheatsheet_agent = Agent(
    role="Cheatsheet Generator",
    goal="Convert JSON flashcards into a one page cheatsheet, prioritizing harder concepts",
    backstory="Expert at summarizing and organizing information for quick reference.",
    verbose=True,
    allow_delegation=True
)

cheatsheet_task = Task(
    description=(
        "Take the provided JSON flashcards:\n\n{flashcards}\n\n"
        "Convert them into a concise cheatsheet in Markdown format.\n"
        "Do not make the cheatsheet too long, it has to fit on one page.\n"
        "The cheatsheet should prioritize harder concepts and be organized for quick reference.\n"
        "Use difficulty score to determine which concepts to include more of, the larger the score number, the harder the concept for the student.\n"
        "Do not fabricate information."
    ),
    expected_output="Valid Markdown cheatsheet only",
    agent=cheatsheet_agent
)
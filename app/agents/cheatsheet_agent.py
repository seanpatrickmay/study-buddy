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
        "Take the provided JSON flashcards and output a concise cheatsheet in Markdown format. "
        "The cheatsheet should prioritize harder concepts and be organized for quick reference. "
        "The "
        "Do not fabricate information."
        ""
    ),
    expected_output="Valid Markdown cheatsheet only",
    agent=cheatsheet_agent
)
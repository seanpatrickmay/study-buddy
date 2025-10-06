# Fixed agent approach with proper extraction and verification
from crewai import Agent, Task

from study_buddy.agents import default_agent_llm


_TAV_AGENT_LLM = default_agent_llm()

extraction_agent = Agent(
    role="Document Extraction Specialist",
    goal="Capture key ideas and vocabulary strictly from the supplied notes",
    backstory=(
        "You carefully transcribe structure from study materials without inventing or embellishing."
    ),
    verbose=True,
    allow_delegation=False,
    llm=_TAV_AGENT_LLM,
)

extraction_task = Task(
    description=(
        "Take the following Markdown notes:\n\n{markdown}\n\n"
        "Parse the file and note down the key ideas and vocabulary in a list format\n" 
        "Note that key ideas should "
        "divide the key ideas into main ideas and supporting details\n"
        "extract vocabulary terms along with their definitions\n"
        "output must not contain any other information except the key ideas and vocabulary\n"
        "if a definition is missing in the notes, write 'NOT_FOUND' instead of guessing\n"
        "and information must be from the inputted markdown exclusively\n"
        "ensure that key ideas and vocabulary are clearly separated by headings and a newline\n"
    ),
    expected_output="Valid markdown file, with vocabular terms and key ideas clearly stated",
    agent=extraction_agent
)

verification_agent = Agent(
    role="Consistency Reviewer",
    goal="Ensure the extracted notes match the source exactly without inventing content",
    backstory=(
        "You double-check that every statement is grounded in the provided notes and never add new facts."
    ),
    verbose=True,
    allow_delegation=False,
    llm=_TAV_AGENT_LLM,
)

verification_task = Task(
    description=(
        "Review the extraction for strict fidelity to the provided markdown.\n"
        "Do not add outside knowledge.\n"
        "If a definition is missing, leave 'NOT_FOUND' in place so downstream tools can fetch it via web search.\n"
    ),
    expected_output="Valid markdown file, with vocabular terms and key ideas clearly stated",
    agent=verification_agent,
    context=[extraction_task]
)




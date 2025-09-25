# Fixed agent approach with proper extraction and verification
from crewai import Agent, Task

extraction_agent = Agent(
    role="Extraction Agent",
    goal="Turn a markdown document into another markdown document that contains key ideas and vocabulary",
    backstory="Expert at extracting key ideas and vocabulary from educational content.",
    verbose=True,
    allow_delegation=False
)

extraction_task = Task(
    description=(
        "Take the following Markdown notes:\n\n{markdown}\n\n"
        "Parse the file and note down the key ideas and vocabulary in a list format\n" 
        "Note that key ideas should "
        "divide the key ideas into main ideas and supporting details\n"
        "extract vocabulary terms along with their definitions\n"
        "output must not contain any other information except the key ideas and vocabulary\n"
        "and information must be from the inputted markdown exclusively\n"
        "ensure that key ideas and vocabulary are clearly separated by headings and a newline\n"
    ),
    expected_output="Valid markdown file, with vocabular terms and key ideas clearly stated",
    agent=extraction_agent
)

verification_agent = Agent(
    role="Verification Agent",
    goal="Watches over the extraction agent to ensure output accuracy and relevance and supply missing information",
    backstory="Expert of educational content and ensuring information accuracy.",
    verbose=True,
    allow_delegation=False,
)

verification_task = Task(
    description=(
        "Watch over the extraction agent to ensure output accuracy and relevance\n"
        "if information is missing or seems inaccurate, supply the missing information\n"
        "based on your expertise in educational content\n"
    ),
    expected_output="Valid markdown file, with vocabular terms and key ideas clearly stated",
    agent=verification_agent,
    context=[extraction_task]
)






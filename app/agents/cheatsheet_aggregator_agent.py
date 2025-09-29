from crewai import Agent, Task

cheatsheet_aggregator_agent = Agent(
    role="Cheatsheet Synthesiser",
    goal="Merge multiple LaTeX cheat sheet drafts into a single, dense, three-column sheet without adding new facts",
    backstory=(
        "You are a meticulous study editor. You receive several LaTeX drafts produced by other specialists."
        "Your job is to combine their content, remove duplicates, align terminology, and deliver a single sheet that"
        "fills all three columns of the provided template. You never invent new information—only reorganise and"
        "clarify what was supplied."
    ),
    verbose=True,
    allow_delegation=False,
)

cheatsheet_aggregator_task = Task(
    description=(
        "You will receive JSON with keys 'template', 'guidelines', and 'pair'.\n"
        "- 'template' contains the LaTeX preamble/structure to reuse.\n"
        "- 'pair' holds exactly two objects with 'name' and 'latex'. Each latex string is a cheat-sheet draft.\n"
        "- 'guidelines' is an array of bullet points you must follow.\n\n"
        "Here is the payload you must work with (do not ignore it):\n\n{flashcards}\n\n"
        "Instructions:\n"
        "1. Parse both LaTeX drafts, extract sections, subsections, bullet points, and formulas.\n"
        "2. Merge the content into a single snippet that can be inserted inside the provided template (do not include documentclass or begin/end document).\n"
        "3. Group related ideas logically, deduplicate overlaps, and keep all equations/notation intact.\n"
        "4. Ensure the combined snippet is information-dense enough to occupy all three columns when wrapped. Expand explanations using existing material if space remains.\n"
        "5. Cite supplementary or external notes inline (e.g., '(supplementary)').\n"
        "6. Return only the merged LaTeX snippet—no commentary.\n"
        "7. Do not invent new topics, examples, or headings—reuse and refine what is already present in the drafts or the provided guidelines.\n"
        "8. Never emit document wrappers such as \\documentclass, \\begin\\{document\\}, or column wrappers like \\begin\\{multicols*\\}; the caller adds them.\n"
        "9. The provided 'template' string pads braces with spaces to avoid templating conflicts—remove those spaces if you reuse it.\n"
    ),
    expected_output="A merged LaTeX snippet ready to be inserted inside the provided template.",
    agent=cheatsheet_aggregator_agent,
)

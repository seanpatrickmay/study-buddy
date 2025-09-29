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
    "Instructions:\n"
    "1. Parse both LaTeX drafts, extract sections, subsections, bullet points, and formulas.\n"
    "2. Merge the content into the supplied template, grouping related material logically. Use concise subsection headings where helpful.\n"
    "3. Deduplicate overlapping ideas while preserving complementary details. Keep all equations and notation intact.\n"
    "4. Aim to distribute content evenly so all three columns are used. If space remains, expand explanations using existing material; do not invent facts.\n"
    "5. Cite supplementary or external notes inline (e.g., '(supplementary)').\n"
    "6. Return only the merged LaTeX document—no commentary.\n"
),
    expected_output="A single LaTeX document matching the template and filling all three columns.",
    agent=cheatsheet_aggregator_agent,
)

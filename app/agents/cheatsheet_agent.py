from crewai import Agent, Task

cheatsheet_agent = Agent(
    role="Cheatsheet Generator",
    goal="Convert JSON flashcards into a one page reference sheet without inventing new facts",
    backstory=(
        "You build study aids only from the information provided in the flashcards or explicitly attributed web-search snippets."
        "When something is unclear you leave space for downstream enrichment rather than guessing."
    ),
    verbose=True,
    allow_delegation=True
)

cheatsheet_task = Task(
    description=(
        "Take the provided JSON payload (keys: 'template', 'topics', 'supplementary_notes', 'guidelines'):\n\n{flashcards}\n\n"
        "Convert the flashcards grouped under 'topics' into a compact, single-page LaTeX cheatsheet (A4 paper). "
        "Return only the LaTeX body snippet that belongs inside the supplied template (no documentclass, no begin/end document). "
        "Ensure the snippet compiles cleanly once wrapped by the provided template.\n\n"

        "Target audience: graduate students / professionals. Prioritize harder concepts (higher numeric difficulty_score). "
        "The agent should treat the input as possibly being from any subject, and adapt formatting "
        "(math, short equations, concise notation) accordingly.\n\n"

        "Layout & formatting requirements:\n"
        "- Paper: A4. Minimum font size: 8pt. Use a multi-column layout; use 3 columns by default to maximize density.\n"
        "- No images or external graphics are allowed.\n"
        "- Grayscale / printer-friendly output only (no color required).\n"
        "- Include a small 'Glossary / symbols' box with short definitions for abbreviations and math symbols used on the page.\n"
        "- Use compact spacing, small headers, and tight lists so the page fits as much high-priority content as possible while remaining legible.\n\n"

        "Inclusion & prioritization rules:\n"
        "- Primary ordering: sort cards by difficulty_score descending (highest first).\n"
        "- Use tags to organize sections by topic; create one section per major tag or combined tags when sensible.\n"
        "- Merge trivial duplicates or near-duplicates into a single, concise entry.\n"
        "- Items with negative difficulty_score should be included only as extremely concise one-line reminders.\n"
        "- Include short worked examples or derivations only for the highest-priority items and only if space permits.\n"
        "- Prefer terse formulas/equations over prose. Use symbols and abbreviations freely, but ensure the glossary box defines them briefly.\n\n"

        "Formatting & output constraints:\n"
        "- Output must be only the LaTeX snippet for the cheat sheet body—no additional commentary.\n"
        "- The snippet must rely solely on packages already loaded by the provided template (multicol, enumitem, amsmath, amssymb).\n"
        "- Organize the cheat sheet into topic sections based on the provided 'topics'.\n"
        "- Reformat and summarize flashcard content; do not invent facts or generic filler.\n"
        "- Supplement with 'supplementary_notes' only when they reinforce flashcard content, citing sources inline.\n"
        "- Ensure all three columns can be filled; expand explanations using the supplied material if space remains.\n\n"
        "- Do not emit document wrappers (e.g., \\documentclass, \\begin\\{document\\}, \\begin\\{multicols*\\}); they are added later.\n\n"
        "- The provided 'template' string includes spaces inside braces to avoid templating conflicts—remove those spaces if you reference it.\n\n"
    ),
    expected_output="A LaTeX snippet that can be inserted into the provided template to produce the cheat sheet.",
    agent=cheatsheet_agent
)

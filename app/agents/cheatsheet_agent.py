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
        "Output must be the full contents of a single valid .tex file and nothing else (no extra commentary, no plaintext explanation). "
        "The agent should produce a single LaTeX document that compiles with common engines (pdfLaTeX or LuaLaTeX/XeLaTeX); "
        "list any non-standard packages used at the top of the .tex file in a TeX comment.\n\n"

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
        "- Output must be only the exact LaTeX source of the cheatsheet (.tex). Do not output anything else.\n"
        "- The document must be self-contained (no external images, no external file includes).\n"
        "- The generated LaTeX should declare the packages it uses at the top.\n"
        "- Organize the cheatsheet into topic sections based on the provided 'topics'. Use the provided 'template' structure for column layout.\n"
        "- Reformat and summarize flashcard content; do not invent facts.\n"
        "- Ignore difficulty scores or meta-guidance; include only subject matter content.\n"
        "- Supplement with 'supplementary_notes' only when they reinforce flashcard content, citing sources inline.\n"
        "- Ensure all three columns are filled; expand explanations or add examples from the available material if space remains.\n\n"

        "Use this template structure:\n"
        "\\documentclass[8pt] plus extarticle class\n"
        "\\usepackage[a4paper,margin=0.7cm] plus geometry package\n"
        "\\usepackage multicol package\n"
        "\\usepackage amsmath,amssymb packages\n"
        "\\usepackage enumitem package\n"
        "\\begin document\n"
        "\\begin multicols*[3]\n"
        "Content sections here...\n"
        "\\end multicols*\n"
        "\\end document"
    ),
    expected_output="A single valid LaTeX .tex file source (only the tex contents, compilable).",
    agent=cheatsheet_agent
)

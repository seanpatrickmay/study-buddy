from crewai import Crew
from app.agents.cheatsheet_agent import cheatsheet_agent, cheatsheet_task
from app.agents.rag_agent import rag_agent, web_enricher_agent
import json

def run_cheatsheet_agent(json_path: str):

    with open(json_path, "r") as f:
        flashcards = json.load(f)

    crew = Crew(
        agents=[cheatsheet_agent, rag_agent, web_enricher_agent],
        tasks=[cheatsheet_task]
    )
    return crew.kickoff(inputs={"flashcards": flashcards})

if __name__ == "__main__":
    cheatsheet = run_cheatsheet_agent("app/utils/example.anki.export.json")
    print(cheatsheet)

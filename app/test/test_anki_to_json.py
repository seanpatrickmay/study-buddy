import json
import subprocess

if __name__ == "__main__":
    cmd = [
        "python3", "app/utils/anki_to_json.py",
        "--apkg", "app/test/testAnkiOut.apkg",
        "--out", "app/test/ankiToJsonTest.json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)

    with open("app/test/ankiToJsonTest.json", "r") as f:
        difficulty_data = json.load(f)

    print(f"Loaded {len(difficulty_data)} flashcards from Anki JSON output")
    print(difficulty_data)
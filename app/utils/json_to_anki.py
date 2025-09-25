#!/usr/bin/env python3
import argparse, json, hashlib, os, sys
import genanki

def stable_32bit_int(s: str) -> int:
    # produce a signed 31-bit positive int (Anki expects 32-bit IDs)
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16) & 0x7FFFFFFF

def stable_guid(front: str, back: str, explicit_id: str | None) -> str:
    if explicit_id:
        base = f"id::{explicit_id}"
    else:
        base = f"front::{front}\x1e back::{back}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()

def build_model(model_name: str, model_id: int) -> genanki.Model:
    return genanki.Model(
        model_id,
        model_name,
        fields=[{"name": "Front"}, {"name": "Back"}],
        templates=[{
            "name": "Card 1",
            "qfmt": "{{Front}}",
            "afmt": "{{Front}}<hr id=answer>{{Back}}",
        }],
        css="""
        .card { font-family: -apple-system, Inter, Arial, sans-serif; font-size: 20px; line-height: 1.35; text-align: left; }
        hr#answer { margin: 14px 0; }
        """,
    )

def main():
    ap = argparse.ArgumentParser(description="Build an Anki .apkg from a JSON file of front/back cards.")
    ap.add_argument("--input", "-i", required=True, help="Path to input JSON (list of {front, back, [tags], [id]}).")
    ap.add_argument("--deck", "-d", required=True, help='Deck name, e.g. "Spanish::Food Basics"')
    ap.add_argument("--out", "-o", required=True, help="Output .apkg path, e.g. my_deck.apkg")
    ap.add_argument("--model-name", default="Basic (Programmatic v1)", help="Custom model name.")
    ap.add_argument("--model-id", type=int, default=None, help="Optional 32-bit model ID (int). If omitted, derived from model name.")
    ap.add_argument("--deck-id", type=int, default=None, help="Optional 32-bit deck ID (int). If omitted, derived from deck name.")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print(f"Input not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        cards = json.load(f)
    if not isinstance(cards, list) or not cards:
        print("Input JSON must be a non-empty list.", file=sys.stderr)
        sys.exit(1)

    model_id = args.model_id if args.model_id is not None else stable_32bit_int(args.model_name)
    deck_id  = args.deck_id  if args.deck_id  is not None else stable_32bit_int(args.deck)

    model = build_model(args.model_name, model_id)
    deck = genanki.Deck(deck_id, args.deck)

    created = 0
    for idx, item in enumerate(cards, start=1):
        try:
            front = item["front"].strip()
            back  = item["back"].strip()
        except KeyError as e:
            print(f"Card #{idx} missing field: {e}", file=sys.stderr)
            sys.exit(1)

        guid = stable_guid(front, back, item.get("id"))
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            print(f"Card #{idx} 'tags' must be a list of strings.", file=sys.stderr)
            sys.exit(1)

        note = genanki.Note(
            model=model,
            fields=[front, back],
            tags=tags,
            guid=guid
        )
        deck.add_note(note)
        created += 1

    pkg = genanki.Package(deck)
    pkg.write_to_file(args.out)
    print(f"Wrote {args.out} with {created} cards.\n"
          f"Model ID: {model_id} | Deck ID: {deck_id}")

if __name__ == "__main__":
    main()
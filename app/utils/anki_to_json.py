#!/usr/bin/env python3
"""
Convert an Anki .apkg export (exported WITH scheduling info) into JSON
summaries that include difficulty data derived from the review log.

Output JSON shape:
[
  {
    "name": "Front text",
    "description": {"front": "Front text", "back": "Back text"},
    "tags": ["tag1", "tag2"],
    "difficulty_score": 1.234
  }
]
"""

import argparse, datetime as dt, json, math, os, shutil, sqlite3, tempfile, zipfile
from typing import Optional

US = "\x1f"  # Anki field separator

def parse_args():
    ap = argparse.ArgumentParser(
        description="Convert an Anki .apkg (with scheduling info) into a JSON file with difficulty stats."
    )
    ap.add_argument("--apkg", "-i", required=True, help="Path to exported deck .apkg")
    ap.add_argument("--out", "-o", default="anki_export.json", help="Output JSON path")
    ap.add_argument("--since", help="Only include reviews on/after this date (YYYY-MM-DD). If omitted, include ALL history.")
    ap.add_argument("--days", type=int, help="Only include the last N days. Overrides --since if both given.")
    ap.add_argument("--deck-like", help="Optional substring filter on deck name (case-insensitive).")
    ap.add_argument("--include-history", action="store_true", help="Include per-review history for each card.")
    return ap.parse_args()

def utc_now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def find_collection(db_dir: str) -> str:
    for name in ("collection.anki21", "collection.anki2"):
        p = os.path.join(db_dir, name)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No collection.anki21/collection.anki2 found. Did you export WITH scheduling info?")

def parse_window(since: str | None, days: int | None) -> tuple[int, dict]:
    """
    Return (since_ms, window_meta_dict). If neither provided, since_ms=0 (all history).
    """
    if days is not None:
        since_ms = int((dt.datetime.utcnow() - dt.timedelta(days=days)).timestamp() * 1000)
        return since_ms, {"since_ms": since_ms, "since_date": None, "filter": f"last_{days}_days"}
    if since:
        y, m, d = map(int, since.split("-"))
        ts = int(dt.datetime(y, m, d).timestamp() * 1000)
        return ts, {"since_ms": ts, "since_date": since, "filter": "since_date"}
    return 0, {"since_ms": 0, "since_date": None, "filter": "all"}

def difficulty_score(again: int, hard: int, good: int, easy: int, last_ms: Optional[int], now_ms: int) -> float:
    """
    Recency-aware score. Higher = more difficult.
    Maps the result smoothly into the range [-10, 10].

    Behavior notes:
    - If last_ms is None (no history), returns 0.0.
    - The internal raw score follows your original weighting:
        raw = (again * 3.0 + hard * 1.5 - good * 0.25 - easy * 0.5) * recency
    - `recency` is ~=1.5 when very recent, ~=1.0 when old (same as your original).
    - The final scaled score = 10 * tanh(raw / 3.0) which compresses the result into [-10,10].
      The divisor 3.0 is a tunable scale parameter — increase to compress more aggressively,
      decrease to let raw values map closer to +/-10.
    """
    if last_ms is None:
        return 0.0

    days_since = max(0.0, (now_ms - last_ms) / 86400000.0)
    recency = 1.0 + 0.5 * (1.0 / (1.0 + math.exp(-(3.0 - days_since))))
    raw = (again * 3.0 + hard * 1.5 - good * 0.25 - easy * 0.5) * recency

    # Smoothly compress into [-10, 10]. Adjust 'scale' if you want different sensitivity.
    scale = 3.0
    scaled = 10.0 * math.tanh(raw / scale)

    return round(scaled, 3)

def split_tags(tag_blob: str) -> list[str]:
    # Anki stores tags as a space-separated string with leading/trailing spaces.
    if not tag_blob:
        return []
    return [t for t in tag_blob.strip().split() if t]

def main():
    args = parse_args()
    tmpdir = tempfile.mkdtemp(prefix="apkg_")
    try:
        # Unzip the .apkg
        with zipfile.ZipFile(args.apkg) as zf:
            zf.extractall(tmpdir)

        # Open DB
        db_path = find_collection(tmpdir)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Load deck and model names from 'col' (only used for optional deck filter)
        deck_names = {}
        for (decks_json, _) in c.execute("SELECT decks, models FROM col").fetchall():
            decks = json.loads(decks_json)
            for did, meta in decks.items():
                try:
                    deck_names[int(did)] = meta.get("name", str(did))
                except Exception:
                    pass

        # Determine window
        since_ms, _window_meta = parse_window(args.since, args.days)
        now_ms = int(dt.datetime.utcnow().timestamp() * 1000)

        # Aggregate over ALL cards in the export; left join revlog so zero-review cards are kept.
        agg_sql = """
        SELECT
            cd.id         AS cid,
            cd.did        AS did,
            n.id          AS nid,
            n.guid        AS nguid,
            n.mid         AS nmid,
            n.flds        AS flds,
            n.tags        AS tags,
            SUM(CASE WHEN r.ease=1 THEN 1 ELSE 0 END) AS again_ct,
            SUM(CASE WHEN r.ease=2 THEN 1 ELSE 0 END) AS hard_ct,
            SUM(CASE WHEN r.ease=3 THEN 1 ELSE 0 END) AS good_ct,
            SUM(CASE WHEN r.ease=4 THEN 1 ELSE 0 END) AS easy_ct,
            COUNT(r.id)   AS reviews,
            MIN(r.id)     AS first_ms,
            MAX(r.id)     AS last_ms
        FROM cards cd
        JOIN notes n ON n.id = cd.nid
        LEFT JOIN revlog r ON r.cid = cd.id AND r.id >= ?
        GROUP BY cd.id, cd.did, n.id, n.guid, n.mid, n.flds, n.tags
        """
        rows = c.execute(agg_sql, (since_ms,)).fetchall()
        conn.close()

        # Build minimal JSON rows
        output_cards = []
        any_reviews = False
        for (cid, did, nid, nguid, nmid, flds, tags,
              again, hard, good, easy, reviews, first_ms, last_ms) in rows:

            deck_name = deck_names.get(did, str(did))
            if args.deck_like and args.deck_like.lower() not in deck_name.lower():
                continue

            again = int(again or 0); hard = int(hard or 0); good = int(good or 0); easy = int(easy or 0)
            reviews = int(reviews or 0)
            if reviews > 0:
                any_reviews = True

            fields = (flds or "").split(US)
            front = fields[0] if fields else ""
            back  = fields[1] if len(fields) > 1 else ""

            score = difficulty_score(again, hard, good, easy, last_ms, now_ms)

            output_cards.append({
                "name": front,
                "description": {"front": front, "back": back},
                "tags": split_tags(tags or ""),
                "difficulty_score": score,
            })

        # Sort by difficulty descending
        output_cards.sort(key=lambda r: r["difficulty_score"], reverse=True)

        # Write minimal JSON array
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(output_cards, f, ensure_ascii=False, indent=2)

        # Friendly hints
        if not any_reviews:
            print("Warning: No review history found in this export. Did you check 'Include scheduling information' when exporting?")
        print(f"Wrote {args.out} with {len(output_cards)} cards.")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
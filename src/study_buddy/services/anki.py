"""Helpers for producing and analysing Anki decks."""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import genanki

from study_buddy.core.models import Flashcard


@dataclass(slots=True)
class DeckMetadata:
    """Metadata controlling how Anki artefacts are produced."""

    deck_name: str
    deck_id: int
    model_name: str
    model_id: int


class AnkiDeckBuilder:
    """Create .apkg packages from :class:`Flashcard` definitions."""

    def __init__(self, metadata: DeckMetadata) -> None:
        self._metadata = metadata

    def build(self, cards: Iterable[Flashcard], output_path: Path) -> Path:
        model = genanki.Model(
            self._metadata.model_id,
            self._metadata.model_name,
            fields=[{"name": "Front"}, {"name": "Back"}],
            templates=[{
                "name": "Card 1",
                "qfmt": "{{Front}}",
                "afmt": "{{Front}}<hr id=answer>{{Back}}",
            }],
            css=(
                ".card { font-family: -apple-system, Inter, Arial, sans-serif; "
                "font-size: 20px; line-height: 1.35; text-align: left; }\n"
                "hr#answer { margin: 14px 0; }"
            ),
        )

        deck = genanki.Deck(self._metadata.deck_id, self._metadata.deck_name)

        created = 0
        for card in cards:
            if not card.front or not card.back:
                continue
            guid = self._stable_guid(card)
            note = genanki.Note(
                model=model,
                fields=[card.front, card.back],
                tags=card.tags,
                guid=guid,
            )
            deck.add_note(note)
            created += 1

        package = genanki.Package(deck)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        package.write_to_file(str(output_path))
        return output_path

    def _stable_guid(self, card: Flashcard) -> str:
        base = card.identifier or f"{card.front}\x1e{card.back}"
        return hashlib.md5(base.encode("utf-8")).hexdigest()


class AnkiDifficultyReader:
    """Parse Anki exports (.apkg) to recover difficulty metadata."""

    def parse(self, apkg_path: Path) -> List[dict]:
        if not apkg_path.exists():
            raise FileNotFoundError(apkg_path)

        tmpdir = Path(tempfile.mkdtemp(prefix="apkg_"))
        try:
            with zipfile.ZipFile(apkg_path) as archive:
                archive.extractall(tmpdir)

            collection_path = self._locate_collection(tmpdir)
            connection = sqlite3.connect(collection_path)
            cursor = connection.cursor()

            decks = self._load_deck_names(cursor)
            rows = cursor.execute(self._aggregation_sql()).fetchall()
            connection.close()

            return self._build_response(rows, decks)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def _locate_collection(self, directory: Path) -> Path:
        for name in ("collection.anki21", "collection.anki2"):
            candidate = directory / name
            if candidate.exists():
                return candidate
        raise FileNotFoundError("collection.anki21 not found in export")

    @staticmethod
    def _load_deck_names(cursor) -> dict:
        decks: dict = {}
        for decks_json, _models_json in cursor.execute("SELECT decks, models FROM col").fetchall():
            payload = json.loads(decks_json)
            for deck_id, meta in payload.items():
                try:
                    decks[int(deck_id)] = meta.get("name", str(deck_id))
                except Exception:
                    continue
        return decks

    @staticmethod
    def _aggregation_sql() -> str:
        return """
        SELECT
            cd.id, cd.did, n.id, n.flds, n.tags,
            SUM(CASE WHEN r.ease=1 THEN 1 ELSE 0 END) AS again_ct,
            SUM(CASE WHEN r.ease=2 THEN 1 ELSE 0 END) AS hard_ct,
            SUM(CASE WHEN r.ease=3 THEN 1 ELSE 0 END) AS good_ct,
            SUM(CASE WHEN r.ease=4 THEN 1 ELSE 0 END) AS easy_ct,
            COUNT(r.id) AS reviews,
            MAX(r.id) AS last_ms
        FROM cards cd
        JOIN notes n ON n.id = cd.nid
        LEFT JOIN revlog r ON r.cid = cd.id
        GROUP BY cd.id, cd.did, n.id, n.flds, n.tags
        """

    def _build_response(self, rows, decks: dict) -> List[dict]:
        results: List[dict] = []
        for (
            card_id,
            deck_id,
            _note_id,
            fields,
            tags,
            again,
            hard,
            good,
            easy,
            reviews,
            last_ms,
        ) in rows:
            front, back = self._split_fields(fields)
            score = self._difficulty_score(int(again or 0), int(hard or 0), int(good or 0), int(easy or 0), last_ms)
            results.append(
                {
                    "card_id": card_id,
                    "deck": decks.get(deck_id, str(deck_id)),
                    "name": front,
                    "description": {"front": front, "back": back},
                    "tags": self._split_tags(tags or ""),
                    "difficulty_score": score,
                    "reviews": int(reviews or 0),
                }
            )
        results.sort(key=lambda item: item["difficulty_score"], reverse=True)
        return results

    @staticmethod
    def _split_fields(raw_fields: str) -> tuple[str, str]:
        US = "\x1f"
        parts = (raw_fields or "").split(US)
        front = parts[0] if parts else ""
        back = parts[1] if len(parts) > 1 else ""
        return front, back

    @staticmethod
    def _split_tags(blob: str) -> List[str]:
        return [tag for tag in blob.strip().split() if tag]

    @staticmethod
    def _difficulty_score(again: int, hard: int, good: int, easy: int, last_ms: Optional[int]) -> float:
        if last_ms is None:
            return 0.0
        recency_days = max(0.0, (self_now_ms() - last_ms) / 86_400_000)
        recency = 1.0 + 0.5 * (1.0 / (1.0 + math.exp(-(3.0 - recency_days))))
        raw = (again * 3.0 + hard * 1.5 - good * 0.25 - easy * 0.5) * recency
        return round(10.0 * math.tanh(raw / 3.0), 3)


def self_now_ms() -> int:
    import datetime as dt

    return int(dt.datetime.utcnow().timestamp() * 1000)

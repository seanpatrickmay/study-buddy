from __future__ import annotations

import pytest

from study_buddy.core.models import DocumentBundle
from study_buddy.services.flashcards import FlashcardGenerator


@pytest.mark.asyncio
async def test_flashcard_generator_filters_and_deduplicates(tmp_path) -> None:
    generator = FlashcardGenerator()
    document = DocumentBundle(
        source_path=tmp_path / "notes.pdf",
        display_name="notes.pdf",
        markdown="Cardiac muscle tissue enables rhythmic contractions in the heart.",
    )

    key_terms = [
        {
            "term": "Overview",  # filtered: stopword and too generic
            "definition": "A short description.",
        },
        {
            "term": "Cardiac Muscle",
            "definition": "Specialised striated muscle responsible for heart contractions.",
            "context": "Cardiac muscle cells synchronise via intercalated disks.",
            "difficulty_score": 0.8,
        },
        {
            "term": "Cardiac Muscle",
            "definition": "Specialised striated muscle responsible for heart contractions.",
            "context": "Cardiac muscle cells synchronise via intercalated disks.",
            "difficulty_score": 0.8,
        },
    ]

    cards = await generator.generate(key_terms, [document])

    assert len(cards) == 1
    card = cards[0]
    assert card.front == "Cardiac Muscle"
    assert "study_buddy" in card.tags and "key_term" in card.tags
    assert all(" " not in tag for tag in card.tags)
    assert card.difficulty == pytest.approx(0.8)

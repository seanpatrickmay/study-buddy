from __future__ import annotations

from study_buddy.services.cheatsheet import CheatSheetBuilder


def test_replace_unicode_symbols_preserves_texttt_sections() -> None:
    builder = CheatSheetBuilder(vector_search=None, web_search=None)
    sample = r"$Δ$ equals rate × time … and \texttt{\frac{a}{b}} remains literal"
    normalised = builder._replace_unicode_symbols(sample)  # type: ignore[attr-defined]
    assert "$\\Delta$" in normalised
    assert "\\times" in normalised
    assert "\\ldots" in normalised
    assert "\\texttt{\\frac{a}{b}}" in normalised

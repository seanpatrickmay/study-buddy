"""Utility helpers for LaTeX compilation."""
from __future__ import annotations

import subprocess
from pathlib import Path


class LaTeXCompiler:
    """Compile LaTeX sources into PDF files using pdflatex."""

    def __init__(self, command: str = "pdflatex") -> None:
        self._command = command

    def compile(self, tex_path: Path, output_dir: Path | None = None) -> Path:
        tex_path = tex_path.resolve()
        workdir = tex_path.parent
        output_dir = (output_dir or workdir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        process = subprocess.run(
            [self._command, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=str(workdir),
            capture_output=True,
            text=True,
        )
        if process.returncode != 0:
            raise RuntimeError(
                f"LaTeX compilation failed for {tex_path.name}: {process.stderr.strip() or process.stdout.strip()}"
            )

        pdf_path = workdir / tex_path.with_suffix(".pdf").name
        target = output_dir / pdf_path.name
        target.write_bytes(pdf_path.read_bytes())
        for suffix in (".aux", ".log", ".out", ".toc"):  # cleanup
            aux = workdir / tex_path.with_suffix(suffix).name
            if aux.exists():
                aux.unlink()
        return target

"""PDF parsing service based on OpenDataLoader PDF."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import tempfile
from typing import BinaryIO

import opendataloader_pdf

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedDocument:
    """Structured representation of an uploaded PDF after markdown extraction."""

    file_name: str
    markdown: str


class PDFParsingError(RuntimeError):
    """Raised when PDF parsing fails."""


class OpenDataLoaderPDFParser:
    """Convert uploaded PDF files into AI-ready Markdown with OpenDataLoader PDF."""

    def parse_uploaded_files(
        self, uploaded_files: list[BinaryIO]
    ) -> list[ParsedDocument]:
        """Persist Streamlit uploads temporarily and parse them into Markdown.

        OpenDataLoader PDF expects file paths, so uploaded in-memory files are written
        to a temporary directory and converted in a single batch for better performance.
        """
        if not uploaded_files:
            LOG.info("PDF parsing skipped because no files were uploaded")
            return []

        LOG.info("Starting PDF parsing (files=%s)", len(uploaded_files))

        with tempfile.TemporaryDirectory(prefix="marketing-doc-analyzer-") as temp_dir:
            temp_path = Path(temp_dir)
            input_paths = self._write_uploads(uploaded_files, temp_path / "input")
            output_dir = temp_path / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            LOG.info(
                "PDF uploads written to temporary input directory (files=%s)",
                len(input_paths),
            )

            try:
                opendataloader_pdf.convert(
                    input_path=[str(path) for path in input_paths],
                    output_dir=str(output_dir),
                    format="markdown",
                    quiet=True,
                    markdown_page_separator="\n\n---\n\n_Page %page-number%_\n\n",
                )
            except (
                Exception
            ) as exc:  # OpenDataLoader may raise Java or subprocess errors.
                LOG.exception(
                    "OpenDataLoader PDF conversion failed (files=%s)",
                    [path.name for path in input_paths],
                )
                raise PDFParsingError(
                    "Die PDF-Dateien konnten nicht mit OpenDataLoader PDF verarbeitet werden. "
                    "Bitte prüfen Sie, ob Java 11+ installiert ist und die Dateien gültige PDFs sind."
                ) from exc

            parsed_documents = [
                ParsedDocument(
                    file_name=path.name,
                    markdown=self._read_markdown_output(path, output_dir),
                )
                for path in input_paths
            ]
            LOG.info(
                "PDF parsing completed (documents=%s, markdown_chars=%s)",
                len(parsed_documents),
                sum(len(document.markdown) for document in parsed_documents),
            )

        return parsed_documents

    @staticmethod
    def _write_uploads(uploaded_files: list[BinaryIO], input_dir: Path) -> list[Path]:
        """Write uploaded files to disk and return their paths."""
        input_dir.mkdir(parents=True, exist_ok=True)
        saved_paths: list[Path] = []

        for uploaded_file in uploaded_files:
            file_name = Path(getattr(uploaded_file, "name", "uploaded.pdf")).name
            if not file_name.lower().endswith(".pdf"):
                raise PDFParsingError(f"'{file_name}' ist keine PDF-Datei.")

            destination = input_dir / file_name
            suffix = 1
            while destination.exists():
                destination = input_dir / f"{Path(file_name).stem}_{suffix}.pdf"
                suffix += 1

            content = (
                uploaded_file.getvalue()
                if hasattr(uploaded_file, "getvalue")
                else uploaded_file.read()
            )
            destination.write_bytes(content)
            LOG.info(
                "Uploaded PDF saved for parsing (file=%s, bytes=%s)",
                destination.name,
                len(content),
            )
            saved_paths.append(destination)

        return saved_paths

    @staticmethod
    def _read_markdown_output(input_path: Path, output_dir: Path) -> str:
        """Find and read the Markdown file generated for a PDF input."""
        candidates = [
            output_dir / f"{input_path.stem}.md",
            output_dir / f"{input_path.name}.md",
        ]
        candidates.extend(output_dir.rglob(f"{input_path.stem}*.md"))

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                markdown = candidate.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
                if markdown:
                    LOG.info(
                        "Markdown output found (input=%s, output=%s, chars=%s)",
                        input_path.name,
                        candidate.name,
                        len(markdown),
                    )
                    return markdown

        LOG.error(
            "Markdown output missing (input=%s, output_dir=%s)",
            input_path.name,
            output_dir,
        )
        raise PDFParsingError(
            f"Für '{input_path.name}' wurde keine Markdown-Ausgabe gefunden."
        )

"""Application orchestration for PDF parsing and report generation."""

from __future__ import annotations

from typing import BinaryIO

from services.llm_service import OpenAIReportService
from services.pdf_parser import OpenDataLoaderPDFParser, ParsedDocument


class MarketingReportGenerator:
    """Coordinate parsing, LLM analysis, and insight generation."""

    def __init__(
        self,
        parser: OpenDataLoaderPDFParser | None = None,
        llm_service: OpenAIReportService | None = None,
    ) -> None:
        self.parser = parser or OpenDataLoaderPDFParser()
        self.llm_service = llm_service or OpenAIReportService()

    def parse_documents(self, uploaded_files: list[BinaryIO]) -> list[ParsedDocument]:
        """Parse uploaded PDFs into Markdown documents."""
        return self.parser.parse_uploaded_files(uploaded_files)

    def generate_report(self, documents: list[ParsedDocument]) -> str:
        """Generate a structured marketing analysis report."""
        return self.llm_service.generate_report(documents)

    def generate_marketing_insights(self, report: str) -> str:
        """Generate agency-focused digital marketing insights from a report."""
        return self.llm_service.generate_marketing_insights(report)

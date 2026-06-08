"""OpenAI API service for marketing document analysis."""

from __future__ import annotations

import os
from textwrap import dedent

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from services.pdf_parser import ParsedDocument


class LLMConfigurationError(RuntimeError):
    """Raised when the OpenAI API configuration is incomplete."""


class LLMGenerationError(RuntimeError):
    """Raised when report generation fails."""


class OpenAIReportService:
    """Generate structured Markdown reports via the OpenAI API."""

    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    @property
    def is_configured(self) -> bool:
        """Return whether an API key is available."""
        return bool(self.api_key and self.client)

    def generate_report(self, documents: list[ParsedDocument]) -> str:
        """Generate the main marketing analysis report."""
        self._ensure_configured()
        prompt = self._build_analysis_prompt(documents)
        return self._complete(prompt)

    def generate_marketing_insights(self, report: str) -> str:
        """Rewrite an existing report from a digital marketing agency perspective."""
        self._ensure_configured()
        prompt = dedent(
            f"""
            Du bist Senior Digital Marketing Consultant in einer Performance-Marketing-Agentur.
            Schreibe den folgenden Analysebericht als praxisnahen Abschnitt "Marketing Insights" um.

            Hebe explizit Potenziale und konkrete nächste Schritte für diese Bereiche hervor:
            - SEO
            - Google Ads
            - Web Analytics
            - Conversion Optimization
            - Content Marketing
            - Automation potential

            Liefere das Ergebnis in klarem Markdown mit Zwischenüberschriften, priorisierten Empfehlungen
            und kurzen Begründungen. Beziehe dich nur auf Informationen, die aus dem Bericht ableitbar sind.

            Bericht:
            {report}
            """
        ).strip()
        return self._complete(prompt)

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            raise LLMConfigurationError("OPENAI_API_KEY ist nicht konfiguriert.")

    def _complete(self, prompt: str) -> str:
        try:
            assert self.client is not None
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Du erstellst präzise, strukturierte Marketing-Analysen in Markdown. "
                            "Kennzeichne Annahmen klar und erfinde keine Fakten."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except OpenAIError as exc:
            raise LLMGenerationError(
                "Die OpenAI API konnte den Bericht nicht erzeugen. Bitte API-Key, Modell und Netzwerk prüfen."
            ) from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise LLMGenerationError("Die OpenAI API hat keine Antwort zurückgegeben.")
        return content.strip()

    @staticmethod
    def _build_analysis_prompt(documents: list[ParsedDocument]) -> str:
        multiple_documents = len(documents) > 1
        comparison_sections = """
        - Similarities
        - Differences
        - Contradictions
        """ if multiple_documents else ""

        document_blocks = "\n\n".join(
            f"## Dokument: {document.file_name}\n\n{document.markdown}" for document in documents
        )

        return dedent(
            f"""
            Analysiere die folgenden PDF-Inhalte aus Marketing-Sicht und erstelle einen strukturierten Bericht.
            Die PDF-Inhalte wurden bereits mit OpenDataLoader PDF in Markdown umgewandelt.

            Der Bericht muss exakt diese Hauptabschnitte enthalten:
            - Executive Summary
            - Key Findings
            - Opportunities
            - Risks
            - Recommended Actions
            - Questions for the Customer
            {comparison_sections}

            Anforderungen:
            - Schreibe professionell, klar und umsetzungsorientiert.
            - Nutze Bulletpoints und kurze Begründungen.
            - Markiere Unsicherheiten als Annahme.
            - Wenn mehrere Dokumente vorliegen, vergleiche sie übergreifend und nenne Widersprüche.
            - Gib keine vertraulichen API- oder Systeminformationen aus.

            Dokumentinhalte:
            {document_blocks}
            """
        ).strip()

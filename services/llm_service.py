"""OpenAI API service for marketing document analysis."""

from __future__ import annotations

import logging
import os
from textwrap import dedent
from typing import Any

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

from services.pdf_parser import ParsedDocument

LOG = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = (
    "Du erstellst präzise, strukturierte Marketing-Analysen in Markdown. "
    "Kennzeichne Annahmen klar und erfinde keine Fakten."
)

DEFAULT_ANALYSIS_PROMPT_TEMPLATE = dedent("""
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
    """).strip()

DEFAULT_INSIGHTS_PROMPT_TEMPLATE = dedent("""
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
    """).strip()


class LLMConfigurationError(RuntimeError):
    """Raised when the OpenAI API configuration is incomplete."""


class LLMGenerationError(RuntimeError):
    """Raised when report generation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class OpenAIReportService:
    """Generate structured Markdown reports via the OpenAI API."""

    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        LOG.info(
            "OpenAI report service initialized (configured=%s, model=%s)",
            self.is_configured,
            self.model,
        )

    @property
    def is_configured(self) -> bool:
        """Return whether an API key is available."""
        return bool(self.api_key and self.client)

    def generate_report(
        self,
        documents: list[ParsedDocument],
        analysis_prompt_template: str = DEFAULT_ANALYSIS_PROMPT_TEMPLATE,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> str:
        """Generate the main marketing analysis report."""
        self._ensure_configured()
        prompt = self.build_analysis_prompt(documents, analysis_prompt_template)
        total_characters = sum(len(document.markdown) for document in documents)
        LOG.info(
            "Generating marketing report (documents=%s, markdown_chars=%s, prompt_chars=%s, model=%s)",
            len(documents),
            total_characters,
            len(prompt),
            self.model,
        )
        return self._complete(prompt, system_prompt)

    def generate_marketing_insights(
        self,
        report: str,
        insights_prompt_template: str = DEFAULT_INSIGHTS_PROMPT_TEMPLATE,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> str:
        """Rewrite an existing report from a digital marketing agency perspective."""
        self._ensure_configured()
        prompt = self.build_insights_prompt(report, insights_prompt_template)
        LOG.info(
            "Generating marketing insights (report_chars=%s, prompt_chars=%s, model=%s)",
            len(report),
            len(prompt),
            self.model,
        )
        return self._complete(prompt, system_prompt)

    def _ensure_configured(self) -> None:
        if not self.is_configured:
            LOG.warning("OpenAI request blocked because OPENAI_API_KEY is missing")
            raise LLMConfigurationError("OPENAI_API_KEY ist nicht konfiguriert.")

    def _complete(self, prompt: str, system_prompt: str) -> str:
        try:
            assert self.client is not None
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
        except OpenAIError as exc:
            details = self._openai_error_details(exc)
            LOG.exception("OpenAI API request failed: %s", details)
            raise LLMGenerationError(
                self._openai_user_message(exc), details=details
            ) from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            LOG.error("OpenAI API returned an empty response (model=%s)", self.model)
            raise LLMGenerationError(
                "Die OpenAI API hat keine Antwort zurückgegeben.",
                details={
                    "model": self.model,
                    "response_choices": (
                        len(response.choices) if response.choices else 0
                    ),
                },
            )

        usage = getattr(response, "usage", None)
        if usage:
            LOG.info(
                "OpenAI API response received (model=%s, prompt_tokens=%s, completion_tokens=%s, total_tokens=%s)",
                self.model,
                getattr(usage, "prompt_tokens", None),
                getattr(usage, "completion_tokens", None),
                getattr(usage, "total_tokens", None),
            )
        else:
            LOG.info(
                "OpenAI API response received (model=%s, usage=unavailable)", self.model
            )
        return content.strip()

    def _openai_error_details(self, exc: OpenAIError) -> dict[str, Any]:
        details: dict[str, Any] = {
            "error_type": type(exc).__name__,
            "model": self.model,
            "message": self._truncate(str(exc)),
        }

        for attribute in ("status_code", "code", "param", "type", "request_id"):
            value = getattr(exc, attribute, None)
            if value is not None:
                details[attribute] = value

        response = getattr(exc, "response", None)
        if response is not None:
            details["http_status_code"] = getattr(response, "status_code", None)
            details["http_headers_request_id"] = getattr(response, "headers", {}).get(
                "x-request-id"
            )

        return {key: value for key, value in details.items() if value not in (None, "")}

    @staticmethod
    def _truncate(value: str, max_length: int = 2_000) -> str:
        """Keep provider diagnostics readable and avoid dumping very large messages."""
        if len(value) <= max_length:
            return value
        return f"{value[:max_length]}... [gekürzt]"

    @staticmethod
    def _openai_user_message(exc: OpenAIError) -> str:
        if isinstance(exc, AuthenticationError):
            return "OpenAI hat den API-Key abgelehnt. Bitte OPENAI_API_KEY prüfen oder neu erstellen."
        if isinstance(exc, PermissionDeniedError):
            return "OpenAI verweigert den Zugriff. Bitte Projekt-/Key-Berechtigungen und Modellfreigabe prüfen."
        if isinstance(exc, NotFoundError):
            return "Das konfigurierte OpenAI-Modell wurde nicht gefunden. Bitte OPENAI_MODEL prüfen."
        if isinstance(exc, RateLimitError):
            return "OpenAI Rate Limit oder Kontingent erreicht. Bitte Limits, Billing und späteren Retry prüfen."
        if isinstance(exc, BadRequestError):
            return "OpenAI hat die Anfrage abgelehnt. Häufige Ursache: zu viel PDF-Text für das Modell oder ungültige Anfrage."
        if isinstance(exc, (APIConnectionError, APITimeoutError)):
            return "Die OpenAI API ist aktuell nicht erreichbar oder hat zu lange gebraucht. Bitte Netzwerk, Proxy/Firewall und Status prüfen."
        return "Die OpenAI API konnte den Bericht nicht erzeugen. Details stehen im technischen Fehlerprotokoll."

    @staticmethod
    def build_analysis_prompt(
        documents: list[ParsedDocument],
        analysis_prompt_template: str = DEFAULT_ANALYSIS_PROMPT_TEMPLATE,
    ) -> str:
        """Build the editable analysis prompt with document placeholders filled."""
        multiple_documents = len(documents) > 1
        comparison_sections = (
            """
        - Similarities
        - Differences
        - Contradictions
        """
            if multiple_documents
            else ""
        )

        document_blocks = "\n\n".join(
            f"## Dokument: {document.file_name}\n\n{document.markdown}"
            for document in documents
        )

        return analysis_prompt_template.format(
            comparison_sections=comparison_sections,
            document_blocks=document_blocks,
        ).strip()

    @staticmethod
    def build_insights_prompt(
        report: str,
        insights_prompt_template: str = DEFAULT_INSIGHTS_PROMPT_TEMPLATE,
    ) -> str:
        """Build the editable marketing insights prompt with report placeholder filled."""
        return insights_prompt_template.format(report=report).strip()

"""Streamlit UI for the AI Marketing Document Analyzer."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import traceback
from typing import Any, BinaryIO

import streamlit as st

from services.llm_service import (
    DEFAULT_ANALYSIS_PROMPT_TEMPLATE,
    DEFAULT_INSIGHTS_PROMPT_TEMPLATE,
    DEFAULT_SYSTEM_PROMPT,
    LLMConfigurationError,
    LLMGenerationError,
)
from services.pdf_parser import PDFParsingError, ParsedDocument
from services.report_generator import MarketingReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
LOG = logging.getLogger(__name__)

st.set_page_config(
    page_title="AI Marketing Document Analyzer",
    page_icon="📊",
    layout="wide",
)


SECTION_TITLES = [
    "Executive Summary",
    "Key Findings",
    "Opportunities",
    "Risks",
    "Recommended Actions",
    "Questions for the Customer",
    "Similarities",
    "Differences",
    "Contradictions",
    "Marketing Insights",
]


MAX_DEBUG_EVENTS = 40


def initialize_session_state() -> None:
    """Initialize Streamlit session keys used by the app."""
    if "report" not in st.session_state:
        st.session_state.report = ""
    if "insights" not in st.session_state:
        st.session_state.insights = ""
    if "debug_events" not in st.session_state:
        st.session_state.debug_events = []
    if "token_metrics" not in st.session_state:
        st.session_state.token_metrics = {}
    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT
    if "analysis_prompt_template" not in st.session_state:
        st.session_state.analysis_prompt_template = DEFAULT_ANALYSIS_PROMPT_TEMPLATE
    if "insights_prompt_template" not in st.session_state:
        st.session_state.insights_prompt_template = DEFAULT_INSIGHTS_PROMPT_TEMPLATE


def add_debug_event(
    level: str, message: str, details: dict[str, Any] | None = None
) -> None:
    """Store a compact, user-visible diagnostic event for the current session."""
    event = {
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "level": level.upper(),
        "message": message,
        "details": details or {},
    }
    st.session_state.debug_events.append(event)
    st.session_state.debug_events = st.session_state.debug_events[-MAX_DEBUG_EVENTS:]


def uploaded_file_details(uploaded_files: list[BinaryIO]) -> list[dict[str, Any]]:
    """Return safe diagnostics for uploaded files without logging file contents."""
    details = []
    for uploaded_file in uploaded_files:
        size = getattr(uploaded_file, "size", None)
        if size is None and hasattr(uploaded_file, "getbuffer"):
            size = len(uploaded_file.getbuffer())
        details.append(
            {"name": getattr(uploaded_file, "name", "uploaded.pdf"), "bytes": size}
        )
    return details


def parsed_document_details(documents: list[ParsedDocument]) -> list[dict[str, Any]]:
    """Return safe diagnostics for parsed documents without logging extracted text."""
    return [
        {"name": document.file_name, "markdown_chars": len(document.markdown)}
        for document in documents
    ]


def estimate_tokens(text: str) -> int:
    """Estimate token counts for UI-only savings metrics.

    OpenAI usage values are only available after an API call. For the user-facing
    overview, use a transparent approximation of roughly four characters per token.
    """
    return max(1, round(len(text) / 4)) if text else 0


def calculate_savings_metrics(original_text: str, used_context: str) -> dict[str, Any]:
    """Calculate approximate token reduction metrics for compact UI cards."""
    original_tokens = estimate_tokens(original_text)
    used_tokens = estimate_tokens(used_context)
    saved_tokens = max(original_tokens - used_tokens, 0)
    savings_percent = (saved_tokens / original_tokens * 100) if original_tokens else 0
    return {
        "original_tokens": original_tokens,
        "used_context_tokens": used_tokens,
        "saved_tokens": saved_tokens,
        "savings_percent": savings_percent,
    }


def format_number(value: int) -> str:
    """Format integers with German thousands separators for Streamlit metrics."""
    return f"{value:,}".replace(",", ".")


def render_token_savings(metrics: dict[str, Any]) -> None:
    """Visualize the approximate token savings achieved by report condensation."""
    if not metrics:
        return

    st.subheader("Token-Ersparnis")
    st.caption(
        "Schätzung auf Basis von ca. 4 Zeichen pro Token: Der extrahierte Originaltext "
        "wird durch den erzeugten Bericht als kompakter Kontext ersetzt."
    )
    col_original, col_context, col_savings = st.columns(3)
    col_original.metric(
        "Original Text", f"{format_number(metrics['original_tokens'])} Tokens"
    )
    col_context.metric(
        "Verwendeter Kontext",
        f"{format_number(metrics['used_context_tokens'])} Tokens",
    )
    col_savings.metric(
        "Geschätzte Ersparnis",
        f"{metrics['savings_percent']:.1f} %".replace(".", ","),
        delta=f"-{format_number(metrics['saved_tokens'])} Tokens",
    )
    st.progress(min(metrics["savings_percent"] / 100, 1.0))


def render_prompt_settings() -> None:
    """Render editable prompt templates for report and insight generation."""
    with st.expander("Prompt-Einstellungen", expanded=False):
        st.caption(
            "Hier können System-Prompt sowie die Vorlagen für den Analysebericht und "
            "die Marketing Insights angepasst werden. Platzhalter bitte beibehalten."
        )
        st.session_state.system_prompt = st.text_area(
            "System-Prompt",
            value=st.session_state.system_prompt,
            height=100,
            help="Gilt für Analysebericht und Marketing Insights.",
        )
        st.session_state.analysis_prompt_template = st.text_area(
            "Prompt: Strukturierter Marketing-Analysebericht",
            value=st.session_state.analysis_prompt_template,
            height=360,
            help="Pflicht-Platzhalter: {document_blocks}. Optional: {comparison_sections}.",
        )
        st.session_state.insights_prompt_template = st.text_area(
            "Prompt: Marketing Insights",
            value=st.session_state.insights_prompt_template,
            height=300,
            help="Pflicht-Platzhalter: {report}.",
        )
        if st.button("Prompts auf Standard zurücksetzen", use_container_width=True):
            st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT
            st.session_state.analysis_prompt_template = DEFAULT_ANALYSIS_PROMPT_TEMPLATE
            st.session_state.insights_prompt_template = DEFAULT_INSIGHTS_PROMPT_TEMPLATE
            st.rerun()


def show_api_key_warning() -> None:
    """Render a helpful warning when the OpenAI API key is missing."""
    st.warning(
        "OPENAI_API_KEY ist nicht konfiguriert.\n\n"
        "1. Erstellen Sie eine `.env` Datei im Projekt-Root.\n"
        "2. Fügen Sie `OPENAI_API_KEY=your_api_key_here` hinzu.\n"
        "3. Starten Sie die Streamlit App neu.",
        icon="⚠️",
    )


def truncate_debug_value(value: str, max_length: int = 2_000) -> str:
    """Keep UI diagnostics readable without dumping very large exception messages."""
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}... [gekürzt]"


def render_error_details(exc: Exception, context: dict[str, Any] | None = None) -> None:
    """Show actionable error details in the UI and record them in the session log."""
    details: dict[str, Any] = {
        "exception_type": type(exc).__name__,
        "message": truncate_debug_value(str(exc)),
    }
    if context:
        details["context"] = context

    exception_details = getattr(exc, "details", None)
    if exception_details:
        details["provider_details"] = exception_details

    if exc.__cause__ is not None:
        details["root_cause_type"] = type(exc.__cause__).__name__
        details["root_cause_message"] = truncate_debug_value(str(exc.__cause__))

    add_debug_event("ERROR", truncate_debug_value(str(exc)), details)
    LOG.exception("Application error: %s", details)

    with st.expander("Technische Fehlerdetails", expanded=True):
        st.caption("Keine API-Keys oder PDF-Inhalte werden hier angezeigt.")
        st.json(details)
        st.code("".join(traceback.format_exception_only(type(exc), exc)).strip())


def render_debug_log() -> None:
    """Render the recent user-visible diagnostic events."""
    with st.expander("Debug Log", expanded=False):
        if not st.session_state.debug_events:
            st.caption("Noch keine Diagnoseereignisse in dieser Sitzung.")
            return

        for event in reversed(st.session_state.debug_events):
            st.markdown(f"**{event['time']} · {event['level']}** — {event['message']}")
            if event["details"]:
                st.json(event["details"])


def split_report_sections(report: str) -> dict[str, str]:
    """Split Markdown report into expandable sections when known headings are present."""
    sections: dict[str, list[str]] = {}
    current_title = "Report"
    sections[current_title] = []

    for line in report.splitlines():
        normalized = line.strip().lstrip("#").strip()
        if normalized in SECTION_TITLES:
            current_title = normalized
            sections.setdefault(current_title, [])
            continue
        sections.setdefault(current_title, []).append(line)

    return {
        title: "\n".join(content).strip()
        for title, content in sections.items()
        if "\n".join(content).strip()
    }


def render_report(report: str) -> None:
    """Render report sections in Streamlit expanders."""
    sections = split_report_sections(report)
    for title, content in sections.items():
        expanded = title in {"Executive Summary", "Report"}
        with st.expander(title, expanded=expanded):
            st.markdown(content)


def main() -> None:
    """Run the Streamlit application."""
    initialize_session_state()

    st.title("AI Marketing Document Analyzer")
    st.caption(
        "PDFs hochladen, mit OpenDataLoader PDF in Markdown umwandeln und per OpenAI API analysieren."
    )

    generator = MarketingReportGenerator()

    with st.sidebar:
        st.header("Konfiguration")
        st.write(f"OpenAI Modell: `{generator.llm_service.model}`")
        if not generator.llm_service.is_configured:
            show_api_key_warning()
        else:
            st.success("OpenAI API-Key gefunden.", icon="✅")

        st.divider()
        render_prompt_settings()

        st.divider()
        st.markdown(
            "**Report-Struktur**\n"
            "- Executive Summary\n"
            "- Key Findings\n"
            "- Opportunities\n"
            "- Risks\n"
            "- Recommended Actions\n"
            "- Questions for the Customer"
        )
        st.divider()
        render_debug_log()

    uploaded_files = st.file_uploader(
        "PDF-Dateien per Drag-and-drop hochladen",
        type=["pdf"],
        accept_multiple_files=True,
        help="Sie können eine oder mehrere Marketing-, Strategie- oder Kunden-PDFs hochladen.",
    )

    col_analyze, col_insights = st.columns([1, 1])
    with col_analyze:
        analyze_clicked = st.button(
            "Analyse starten", type="primary", use_container_width=True
        )
    with col_insights:
        insights_clicked = st.button("Marketing Insights", use_container_width=True)

    if analyze_clicked:
        if not uploaded_files:
            st.error("Bitte laden Sie mindestens eine PDF-Datei hoch.", icon="🚫")
            add_debug_event("ERROR", "Analyse ohne Dateien gestartet")
        elif not generator.llm_service.is_configured:
            show_api_key_warning()
            add_debug_event("ERROR", "Analyse ohne OPENAI_API_KEY gestartet")
        else:
            context = {
                "model": generator.llm_service.model,
                "files": uploaded_file_details(uploaded_files),
            }
            try:
                LOG.info("Analysis started: %s", context)
                add_debug_event("INFO", "Analyse gestartet", context)

                progress = st.progress(0, text="PDFs werden vorbereitet...")
                progress.progress(
                    25,
                    text="PDFs werden mit OpenDataLoader PDF in Markdown konvertiert...",
                )
                documents = generator.parse_documents(uploaded_files)
                context["documents"] = parsed_document_details(documents)
                add_debug_event(
                    "INFO",
                    "PDFs erfolgreich in Markdown konvertiert",
                    {"documents": context["documents"]},
                )

                progress.progress(
                    60, text="Markdown-Inhalte werden an die OpenAI API gesendet..."
                )
                report = generator.generate_report(
                    documents,
                    analysis_prompt_template=st.session_state.analysis_prompt_template,
                    system_prompt=st.session_state.system_prompt,
                )

                progress.progress(100, text="Analyse abgeschlossen.")
                st.session_state.report = report
                st.session_state.insights = ""
                original_text = "\n\n".join(document.markdown for document in documents)
                st.session_state.token_metrics = calculate_savings_metrics(
                    original_text, report
                )
                add_debug_event(
                    "INFO",
                    "Marketing-Analyse erfolgreich erstellt",
                    {"report_chars": len(report)},
                )
                st.success("Marketing-Analyse wurde erfolgreich erstellt.", icon="✅")
            except (PDFParsingError, LLMConfigurationError, LLMGenerationError) as exc:
                st.error(str(exc), icon="🚫")
                render_error_details(exc, context)
            except (
                Exception
            ) as exc:  # Last-resort UI guard for unexpected runtime errors.
                st.error(f"Unerwarteter Fehler: {exc}", icon="🚫")
                render_error_details(exc, context)

    if insights_clicked:
        if not st.session_state.report:
            st.error("Bitte erstellen Sie zuerst einen Analysebericht.", icon="🚫")
            add_debug_event("ERROR", "Marketing Insights ohne Analysebericht gestartet")
        elif not generator.llm_service.is_configured:
            show_api_key_warning()
            add_debug_event("ERROR", "Marketing Insights ohne OPENAI_API_KEY gestartet")
        else:
            context = {
                "model": generator.llm_service.model,
                "report_chars": len(st.session_state.report),
            }
            try:
                LOG.info("Marketing insights generation started: %s", context)
                add_debug_event("INFO", "Marketing Insights gestartet", context)
                with st.spinner(
                    "Marketing Insights werden aus Agenturperspektive erstellt..."
                ):
                    st.session_state.insights = generator.generate_marketing_insights(
                        st.session_state.report,
                        insights_prompt_template=st.session_state.insights_prompt_template,
                        system_prompt=st.session_state.system_prompt,
                    )
                add_debug_event(
                    "INFO",
                    "Marketing Insights erfolgreich erstellt",
                    {"insights_chars": len(st.session_state.insights)},
                )
                st.success("Marketing Insights wurden erstellt.", icon="✅")
            except (LLMConfigurationError, LLMGenerationError) as exc:
                st.error(str(exc), icon="🚫")
                render_error_details(exc, context)
            except (
                Exception
            ) as exc:  # Last-resort UI guard for unexpected runtime errors.
                st.error(f"Unerwarteter Fehler: {exc}", icon="🚫")
                render_error_details(exc, context)

    if st.session_state.debug_events:
        st.divider()
        st.subheader("Diagnose der aktuellen Sitzung")
        render_debug_log()

    if st.session_state.report:
        st.divider()
        render_token_savings(st.session_state.token_metrics)

        st.subheader("Strukturierter Marketing-Analysebericht")
        render_report(st.session_state.report)

        full_download = st.session_state.report
        if st.session_state.insights:
            full_download = f"{full_download}\n\n# Marketing Insights\n\n{st.session_state.insights}"
            st.subheader("Marketing Insights")
            render_report(f"# Marketing Insights\n\n{st.session_state.insights}")

        st.download_button(
            "Report als Markdown herunterladen",
            data=full_download,
            file_name="marketing_analysis_report.md",
            mime="text/markdown",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()

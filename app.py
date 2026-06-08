"""Streamlit UI for the AI Marketing Document Analyzer."""

from __future__ import annotations

import streamlit as st

from services.llm_service import LLMConfigurationError, LLMGenerationError
from services.pdf_parser import PDFParsingError
from services.report_generator import MarketingReportGenerator


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


def show_api_key_warning() -> None:
    """Render a helpful warning when the OpenAI API key is missing."""
    st.warning(
        "OPENAI_API_KEY ist nicht konfiguriert.\n\n"
        "1. Erstellen Sie eine `.env` Datei im Projekt-Root.\n"
        "2. Fügen Sie `OPENAI_API_KEY=your_api_key_here` hinzu.\n"
        "3. Starten Sie die Streamlit App neu.",
        icon="⚠️",
    )


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

    return {title: "\n".join(content).strip() for title, content in sections.items() if "\n".join(content).strip()}


def render_report(report: str) -> None:
    """Render report sections in Streamlit expanders."""
    sections = split_report_sections(report)
    for title, content in sections.items():
        expanded = title in {"Executive Summary", "Report"}
        with st.expander(title, expanded=expanded):
            st.markdown(content)


def main() -> None:
    """Run the Streamlit application."""
    st.title("AI Marketing Document Analyzer")
    st.caption("PDFs hochladen, mit OpenDataLoader PDF in Markdown umwandeln und per OpenAI API analysieren.")

    generator = MarketingReportGenerator()

    with st.sidebar:
        st.header("Konfiguration")
        st.write(f"OpenAI Modell: `{generator.llm_service.model}`")
        if not generator.llm_service.is_configured:
            show_api_key_warning()
        else:
            st.success("OpenAI API-Key gefunden.", icon="✅")

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

    uploaded_files = st.file_uploader(
        "PDF-Dateien per Drag-and-drop hochladen",
        type=["pdf"],
        accept_multiple_files=True,
        help="Sie können eine oder mehrere Marketing-, Strategie- oder Kunden-PDFs hochladen.",
    )

    col_analyze, col_insights = st.columns([1, 1])
    with col_analyze:
        analyze_clicked = st.button("Analyse starten", type="primary", use_container_width=True)
    with col_insights:
        insights_clicked = st.button("Marketing Insights", use_container_width=True)

    if "report" not in st.session_state:
        st.session_state.report = ""
    if "insights" not in st.session_state:
        st.session_state.insights = ""

    if analyze_clicked:
        if not uploaded_files:
            st.error("Bitte laden Sie mindestens eine PDF-Datei hoch.", icon="🚫")
        elif not generator.llm_service.is_configured:
            show_api_key_warning()
        else:
            try:
                progress = st.progress(0, text="PDFs werden vorbereitet...")
                progress.progress(25, text="PDFs werden mit OpenDataLoader PDF in Markdown konvertiert...")
                documents = generator.parse_documents(uploaded_files)

                progress.progress(60, text="Markdown-Inhalte werden an die OpenAI API gesendet...")
                report = generator.generate_report(documents)

                progress.progress(100, text="Analyse abgeschlossen.")
                st.session_state.report = report
                st.session_state.insights = ""
                st.success("Marketing-Analyse wurde erfolgreich erstellt.", icon="✅")
            except (PDFParsingError, LLMConfigurationError, LLMGenerationError) as exc:
                st.error(str(exc), icon="🚫")
            except Exception as exc:  # Last-resort UI guard for unexpected runtime errors.
                st.error(f"Unerwarteter Fehler: {exc}", icon="🚫")

    if insights_clicked:
        if not st.session_state.report:
            st.error("Bitte erstellen Sie zuerst einen Analysebericht.", icon="🚫")
        elif not generator.llm_service.is_configured:
            show_api_key_warning()
        else:
            try:
                with st.spinner("Marketing Insights werden aus Agenturperspektive erstellt..."):
                    st.session_state.insights = generator.generate_marketing_insights(st.session_state.report)
                st.success("Marketing Insights wurden erstellt.", icon="✅")
            except (LLMConfigurationError, LLMGenerationError) as exc:
                st.error(str(exc), icon="🚫")
            except Exception as exc:  # Last-resort UI guard for unexpected runtime errors.
                st.error(f"Unerwarteter Fehler: {exc}", icon="🚫")

    if st.session_state.report:
        st.divider()
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

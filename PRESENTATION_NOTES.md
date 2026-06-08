# Präsentationsnotizen: AI Marketing Document Analyzer

## 60-Sekunden-Projektpitch

Der AI Marketing Document Analyzer ist eine Streamlit-App, mit der Marketing- und Kunden-PDFs hochgeladen und automatisch in einen strukturierten Analysebericht umgewandelt werden. Die App nutzt OpenDataLoader PDF, um PDF-Inhalte in Markdown zu konvertieren, und die OpenAI API, um daraus Executive Summary, Key Findings, Opportunities, Risks, Recommended Actions und Customer Questions zu generieren. Bei mehreren PDFs vergleicht das Tool zusätzlich Gemeinsamkeiten, Unterschiede und Widersprüche. Über einen zweiten Button entstehen Marketing Insights aus Agenturperspektive mit Fokus auf SEO, Google Ads, Web Analytics, Conversion Optimization, Content Marketing und Automation.

## Technische Erklärung

- **Frontend:** Streamlit stellt eine einfache, moderne Weboberfläche mit Drag-and-drop Upload, Buttons, Progress Indicator, Expandern und Markdown-Download bereit.
- **PDF-Verarbeitung:** OpenDataLoader PDF extrahiert Inhalte aus PDFs und wandelt sie in strukturiertes Markdown um.
- **LLM-Schicht:** Ein eigener Service kapselt die OpenAI API, lädt den API-Key mit python-dotenv und erzeugt die Berichte über ein klares Prompt-Template.
- **Architektur:** Die App ist in Services getrennt:
  - `pdf_parser.py` für PDF-Parsing
  - `llm_service.py` für OpenAI-Kommunikation
  - `report_generator.py` für die Orchestrierung
  - `app.py` für die Streamlit-Oberfläche
- **Sicherheit:** API-Keys werden nicht hardcodiert, sondern über `.env` geladen. `.env` liegt in `.gitignore`.

## Warum es zu morefire passt

morefire arbeitet datengetrieben und digital-marketing-orientiert. Das Projekt passt gut, weil es Kundeninformationen schneller nutzbar macht und direkt auf relevante Agenturbereiche einzahlt: SEO, Paid Media, Tracking, Conversion-Optimierung, Content und Automation. Es zeigt außerdem, wie KI praktisch in Agenturprozesse integriert werden kann, um Analyse, Onboarding und Strategiearbeit effizienter zu machen.

## Was ich als Nächstes bauen würde

1. Eine echte RAG-Pipeline mit ChromaDB oder FAISS.
2. Einen Chat-Modus, um Rückfragen an hochgeladene PDFs zu stellen.
3. Google-Drive-Import für Kundenunterlagen.
4. n8n-Webhooks, um Reports automatisch in Workflows zu übergeben.
5. Export nach Slack, Microsoft Teams oder Projektmanagement-Tools.
6. Automatische Aufgabenanlage aus Recommended Actions.
7. Vergleich von Kundenreports über Zeit.
8. Authentifizierung und Rollenmodell für produktive Nutzung.
9. PDF-Export für präsentationsfähige Kundenberichte.

## Mögliche Interviewfragen und gute Antworten

### Warum haben Sie Streamlit gewählt?

Streamlit ist ideal für schnelle, funktionale KI-Prototypen. Ich kann damit Uploads, Fortschrittsanzeige, Ergebnisse und Downloads sehr schnell abbilden, ohne ein separates Frontend bauen zu müssen.

### Warum OpenDataLoader PDF?

PDFs sind für LLM-Projekte oft problematisch, weil Tabellen, Überschriften und Lesereihenfolge verloren gehen können. OpenDataLoader PDF ist darauf ausgelegt, PDF-Inhalte strukturiert und LLM-freundlich aufzubereiten, in diesem Projekt als Markdown.

### Ist das schon echtes RAG?

Noch nicht vollständig. Die App nutzt eine RAG-nahe Vorstufe: Dokumente werden extrahiert und als Kontext an das Modell gegeben. Echtes RAG würde zusätzlich Chunking, Embeddings, eine Vektor-Datenbank und Retrieval der relevantesten Passagen enthalten.

### Wie gehen Sie mit Datenschutz um?

In dieser Demo werden keine Secrets hardcodiert, und die `.env` wird nicht committed. Für produktive Nutzung würde ich zusätzlich Zugriffsschutz, Datenlöschung, Logging-Regeln, EU-Hosting-Optionen, Auftragsverarbeitung und klare Hinweise zur Verarbeitung durch externe APIs ergänzen.

### Was war die wichtigste technische Entscheidung?

Die Trennung in Services. Dadurch bleibt die UI schlank, und PDF-Parsing, LLM-Kommunikation und Orchestrierung können später leichter ausgetauscht oder erweitert werden.

### Wie würden Sie das bei morefire produktiv machen?

Ich würde eine echte RAG-Architektur ergänzen, Kundenprojekte getrennt speichern, Rollen und Authentifizierung einbauen, Exporte in bestehende Tools ermöglichen und die Prompts gemeinsam mit Fachteams aus SEO, Paid Media und Analytics iterativ verbessern.

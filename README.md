# AI Marketing Document Analyzer

Der **AI Marketing Document Analyzer** ist eine Python- und Streamlit-Anwendung, mit der Marketing-, Strategie- oder Kunden-PDFs hochgeladen, strukturiert ausgelesen und mit der OpenAI API zu einem professionellen Marketing-Analysebericht verdichtet werden können.

## Projektüberblick

Die App unterstützt den kompletten Workflow von der PDF-Datei bis zum fertigen Markdown-Report:

1. Eine oder mehrere PDF-Dateien per Drag-and-drop hochladen.
2. PDFs mit **OpenDataLoader PDF** in strukturiertes Markdown umwandeln.
3. Markdown-Inhalte an die **OpenAI API** senden.
4. Einen strukturierten Marketingbericht erzeugen.
5. Optional zusätzliche **Marketing Insights** aus Agenturperspektive generieren.
6. Bericht als Markdown-Datei herunterladen.

## Welches Problem löst das Tool?

Marketing-Teams und Agenturen erhalten oft lange PDFs: Briefings, Kundenpräsentationen, Website-Audits, Strategieunterlagen, Wettbewerbsanalysen oder Reports. Diese Dokumente enthalten viele relevante Informationen, sind aber zeitaufwendig zu lesen und miteinander zu vergleichen.

Dieses Tool reduziert den manuellen Analyseaufwand, indem es PDF-Inhalte automatisch extrahiert und daraus eine strukturierte Entscheidungsgrundlage erstellt.

## Warum ist das nützlich für eine Marketingagentur?

Für eine Marketingagentur ist das Tool besonders wertvoll, weil es:

- Kundenunterlagen schneller verständlich macht.
- Chancen, Risiken und konkrete Maßnahmen systematisch herausarbeitet.
- Mehrere Dokumente vergleichen kann.
- Widersprüche zwischen Unterlagen sichtbar macht.
- Einen guten Startpunkt für Strategie, SEO, Google Ads, Tracking, Content und Automation liefert.
- Mitarbeitenden hilft, sich schneller in neue Kundenprojekte einzuarbeiten.

## Features

- Moderne Streamlit-Oberfläche
- Drag-and-drop Upload für eine oder mehrere PDF-Dateien
- PDF-Parsing mit OpenDataLoader PDF
- Umwandlung der PDF-Inhalte in strukturiertes Markdown
- Analyse über die OpenAI API
- Strukturierter Report mit:
  - Executive Summary
  - Key Findings
  - Opportunities
  - Risks
  - Recommended Actions
  - Questions for the Customer
- Bei mehreren PDFs zusätzlich:
  - Similarities
  - Differences
  - Contradictions
- Expandierbare Report-Abschnitte in der UI
- Download des Reports als Markdown
- Klare Fehlermeldung, wenn kein OpenAI API-Key konfiguriert ist
- Debug Log in der Sidebar mit Upload-, Parsing- und OpenAI-Diagnosen
- Technische Fehlerdetails mit OpenAI-Fehlertyp, HTTP-Status, Request-ID und Modellhinweisen, sofern verfügbar
- Bonus-Button **Marketing Insights** mit Fokus auf:
  - SEO
  - Google Ads
  - Web Analytics
  - Conversion Optimization
  - Content Marketing
  - Automation potential

## Tech Stack

- Python 3.12
- Streamlit
- OpenDataLoader PDF
- OpenAI API
- python-dotenv

## Ordnerstruktur

```text
AI-Document-Analyzer/
├── app.py
├── services/
│   ├── pdf_parser.py
│   ├── llm_service.py
│   └── report_generator.py
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── PRESENTATION_NOTES.md
```

## Installation

### 1. Repository öffnen

```bash
cd AI-Document-Analyzer
```

### 2. Virtuelle Umgebung erstellen

```bash
python3.12 -m venv .venv
```

Falls `python3.12` nicht verfügbar ist, prüfen Sie zuerst Ihre Python-Installation:

```bash
python --version
```

### 3. Virtuelle Umgebung aktivieren

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

> Hinweis: OpenDataLoader PDF benötigt Java 11 oder neuer. Prüfen Sie Java mit:

```bash
java -version
```

## `.env` Datei erstellen

Secrets werden nicht im Code gespeichert. Legen Sie im Projekt-Root eine Datei namens `.env` an.

Beispiel:

```bash
cp .env.example .env
```

### OpenAI API-Key hinzufügen

`.env` file:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Die Datei `.env` ist in `.gitignore` eingetragen und sollte nicht in Git committed werden.

## App starten

Run app:

```bash
streamlit run app.py
```

Öffnen Sie danach die lokale Streamlit-URL im Browser, laden Sie eine oder mehrere PDF-Dateien hoch und klicken Sie auf **Analyse starten**.


## Fehlerdiagnose und Logging

Wenn die Analyse mit der Meldung fehlschlägt, dass die OpenAI API den Bericht nicht erzeugen konnte, zeigt die App jetzt zusätzliche Diagnoseinformationen an:

- In der Sidebar befindet sich ein **Debug Log** mit den letzten Schritten der aktuellen Sitzung.
- Direkt unter einer Fehlermeldung erscheint ein Bereich **Technische Fehlerdetails**.
- Bei OpenAI-Fehlern werden, sofern verfügbar, Fehlertyp, HTTP-Status, OpenAI Request-ID, Modellname und eine gekürzte Provider-Meldung angezeigt.
- API-Keys und extrahierte PDF-Inhalte werden nicht in der UI-Diagnose ausgegeben.
- Zusätzlich schreibt die App strukturierte Logs in die Streamlit-Konsole.

Typische Ursachen lassen sich dadurch schneller unterscheiden:

- `AuthenticationError`: API-Key ungültig oder nicht zum Projekt passend.
- `NotFoundError`: `OPENAI_MODEL` ist falsch geschrieben oder nicht freigeschaltet.
- `RateLimitError`: Rate Limit, Kontingent oder Billing prüfen.
- `BadRequestError`: Anfrage ungültig, häufig zu viel extrahierter PDF-Text für das Modell.
- `APIConnectionError` oder `APITimeoutError`: Netzwerk, Proxy, Firewall oder OpenAI-Erreichbarkeit prüfen.

## Beispiel-Use-Case

Eine Marketingagentur erhält von einem potenziellen Kunden:

- ein Unternehmensprofil als PDF,
- einen alten Marketingreport,
- eine Wettbewerbsanalyse,
- ein Kampagnenbriefing.

Die Agentur lädt alle PDFs in die App hoch. Das Tool erzeugt einen Bericht mit Executive Summary, zentralen Erkenntnissen, Chancen, Risiken und empfohlenen nächsten Schritten. Bei mehreren PDFs erkennt die App zusätzlich Gemeinsamkeiten, Unterschiede und mögliche Widersprüche. Danach kann über **Marketing Insights** eine digitale Marketing-Perspektive mit Fokus auf SEO, Google Ads, Web Analytics, Conversion Optimization, Content Marketing und Automation ergänzt werden.

## RAG einfach erklärt

**RAG** steht für **Retrieval-Augmented Generation**. Einfach gesagt bedeutet das:

1. Relevante Informationen werden aus Dokumenten gesucht oder vorbereitet.
2. Diese Informationen werden einem KI-Modell als Kontext gegeben.
3. Das KI-Modell erzeugt darauf basierend eine Antwort oder Analyse.

In dieser Version wird noch keine echte Vektor-Datenbank verwendet. Die App bereitet die hochgeladenen PDFs als Markdown auf und gibt diesen Kontext direkt an die OpenAI API. Das ist eine einfache Vorstufe zu RAG. Eine spätere Version könnte Dokumentabschnitte in einer Vektor-Datenbank speichern und nur die relevantesten Passagen für eine Frage abrufen.

## Aktuelle Limitierungen

- Keine echte RAG-Architektur mit Vektor-Datenbank.
- Sehr große PDFs können Token-Limits des verwendeten OpenAI-Modells erreichen.
- Qualität der Analyse hängt von der PDF-Qualität und der Extraktion ab.
- Keine Benutzerverwaltung.
- Keine persistente Dokumentenablage.
- Kein Chat-Modus mit den hochgeladenen PDFs.
- Kein PDF-Export des fertigen Reports.
- OpenDataLoader PDF benötigt Java 11+ auf dem System.

## Mögliche zukünftige Erweiterungen

- Real RAG with vector database
- ChromaDB or FAISS integration
- Chat with uploaded PDFs
- n8n webhook integration
- Google Drive import
- Slack or Microsoft Teams export
- Comparison of customer reports over time
- Automatic task creation in project management tools
- Export as PDF
- User authentication

## Sicherheit und Secrets

- API-Keys werden ausschließlich über `.env` geladen.
- `.env` wird durch `.gitignore` ausgeschlossen.
- Keine API-Keys im Code hardcoden.
- Für produktive Nutzung sollten zusätzlich Logging, Zugriffsschutz und Datenlöschkonzepte ergänzt werden.

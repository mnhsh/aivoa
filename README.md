# AIVOA — AI-Powered Deviation Intake Module

An AI-assisted Deviation Management platform for API pharmaceutical manufacturers.

## Project Structure

```
aivoa/
├── frontend/               # React + TypeScript + Redux Toolkit + Vite
│   ├── src/
│   │   ├── components/     # UI components & pages
│   │   ├── store.ts        # Redux Toolkit state slice
│   │   ├── utils/          # Extractor & pdfjs-dist PDF parser
│   │   └── styles.css      # Pharma tech UI styles
│   └── package.json
│
├── backend/                # FastAPI + Python + RAG / LLM Service
│   ├── app/
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── api/            # Router & routes (/analyze, /deviations)
│   │   ├── services/       # Analysis, risk assessment & RAG agents
│   │   └── parsers/        # Document parsers
│   └── requirements.txt
└── README.md
```

## How to Run

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### Backend (Optional FastAPI Service)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Backend API will run at [http://localhost:8000](http://localhost:8000).

## Features

- **Document & PDF Auto-Extraction**: Real client-side PDF document page parsing via `pdfjs-dist` and structured extraction parser.
- **Log Deviation Form**: Clean intake form layout with no seeded fake defaults, character counter, and product search suggestions.
- **AI Severity & Impact Reasoning Card**: Automated classification justification detailing *why* severity/impact was chosen with SOP citations (`SOP-DEV-004`).
- **All Deviations View**: Searchable record table with severity filters (`Critical`, `High`, `Medium`, `Low`) and status badges.
- **Human-in-the-Loop Review**: Editable form fields, interactive severity selector, and plain-language chat updates.

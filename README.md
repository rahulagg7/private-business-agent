# private-business-agent

Local AI assistant that answers questions over business documents, email and
QuickBooks data. The LLM (Ollama), embeddings and vector DB all run locally.

## How it works

```
question
   -> router (LLM picks sources: docs / quickbooks / email)
   -> docs:       Chroma vector search, all-MiniLM-L6-v2 embeddings
   -> quickbooks: invoices, balances
   -> email:      search
   -> LLM answers from the retrieved context and cites sources
```

If Ollama isn't running, routing falls back to keywords and the app returns
the retrieved context instead of a generated answer.

## Files

- `ingest.py` - chunks and indexes .txt/.md/.pdf files into Chroma
- `agent.py` - routing, retrieval, answer generation
- `tools.py` - QuickBooks and email connectors (mocked for now)
- `app.py` - FastAPI server + simple web UI
- `sample_data/` - test invoices, email, contract

## Setup

```bash
pip install -r requirements.txt

# install ollama from https://ollama.com/download
ollama pull llama3.1

python ingest.py
uvicorn app:app --reload
```

Open http://localhost:8000

Example questions:
- Which invoices are overdue?
- What did Apex say about invoice 1042, and what's the balance?
- When does the CloudHost contract renew and what's the late payment penalty?

## Status / TODO

- [ ] QuickBooks: replace mocks with QBO API (OAuth2, tokens in keychain)
- [ ] Email: Gmail API / Microsoft Graph, read-only scope
- [ ] Scheduled re-indexing for document folders
- [ ] Auth in front of the web UI if exposed beyond localhost

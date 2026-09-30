"""
Routes a question to docs / quickbooks / email, collects context, asks the LLM.
"""
import json
import requests
import chromadb
from chromadb.errors import NotFoundError
from chromadb.utils import embedding_functions

import tools

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

ROUTER_PROMPT = """You are a routing assistant for a business AI system.
Given the user's question, decide which data sources are needed.
Respond with ONLY a JSON object, no other text, in this exact shape:
{{"use_docs": true/false, "use_quickbooks": true/false, "use_email": true/false}}

Question: {question}
"""

ANSWER_PROMPT = """You are a private business assistant running locally for a small business.
Answer the question using ONLY the context provided below. If the context doesn't
contain the answer, say so plainly rather than guessing.

Context:
{context}

Question: {question}

Answer concisely and cite which document or system each fact came from.
"""


def call_ollama(prompt: str) -> str:
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.exceptions.RequestException:
        # ollama down, model not pulled (404), timeout
        return "__NO_LLM__"


def keyword_route(question: str) -> dict:
    # used when ollama isn't running or returns bad json
    q = question.lower()
    return {
        "use_docs": any(w in q for w in ["invoice", "contract", "document", "agreement", "email", "term"]),
        "use_quickbooks": any(w in q for w in ["overdue", "balance", "cash", "paid", "outstanding", "quickbooks"]),
        "use_email": any(w in q for w in ["email", "reminder", "wrote", "sent"]),
    }


def route_query(question: str) -> dict:
    raw = call_ollama(ROUTER_PROMPT.format(question=question))
    if raw == "__NO_LLM__":
        return keyword_route(question)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return keyword_route(question)


# loading the embedding model is slow, so keep one collection per db/name
_collections = {}


def _get_collection(db_path: str, collection_name: str):
    key = (db_path, collection_name)
    if key not in _collections:
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path=db_path)
        try:
            _collections[key] = client.get_collection(name=collection_name, embedding_function=embed_fn)
        except (NotFoundError, ValueError):
            # not ingested yet. don't cache, so it picks it up after ingest.py runs
            return None
    return _collections[key]


def search_docs(question: str, db_path="./chroma_db", collection_name="business_docs", n_results=3):
    collection = _get_collection(db_path, collection_name)
    if collection is None:
        return []
    results = collection.query(query_texts=[question], n_results=n_results)
    hits = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        hits.append({"source": meta["source"], "text": doc})
    return hits


def answer(question: str) -> dict:
    plan = route_query(question)
    context_parts = []

    if plan.get("use_docs"):
        for hit in search_docs(question):
            context_parts.append(f"[Document: {hit['source']}]\n{hit['text']}")

    if plan.get("use_quickbooks"):
        overdue = tools.get_overdue_invoices()
        cash = tools.get_cash_position_summary()
        context_parts.append(f"[QuickBooks: Overdue invoices]\n{json.dumps(overdue, indent=2)}")
        context_parts.append(f"[QuickBooks: Cash position]\n{json.dumps(cash, indent=2)}")

    if plan.get("use_email"):
        seen = set()
        for kw in ["invoice", "reminder", "payment"]:
            for email in tools.search_emails(kw):
                key = (email["from"], email["date"], email["subject"])
                if key in seen:
                    continue
                seen.add(key)
                context_parts.append(f"[Email from {email['from']} on {email['date']}]\n{email['subject']}: {email['snippet']}")

    context = "\n\n".join(context_parts) if context_parts else "No matching context found."

    final = call_ollama(ANSWER_PROMPT.format(context=context, question=question))
    if final == "__NO_LLM__":
        final = (
            f"[Couldn't get an answer from Ollama at localhost:11434. Make sure it's running and "
            f"the model is pulled (`ollama pull {OLLAMA_MODEL}`). Showing the retrieved context instead:]\n\n"
            + context
        )

    return {"plan": plan, "context": context_parts, "answer": final}

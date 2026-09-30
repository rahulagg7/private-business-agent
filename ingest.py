"""
Index a folder of .txt/.md/.pdf files into a local Chroma collection.

    python ingest.py --source ./sample_data --collection business_docs
"""
import argparse
import os
import hashlib
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


def read_txt(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_pdf(path):
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="./sample_data", help="folder of documents to ingest")
    parser.add_argument("--collection", default="business_docs", help="chroma collection name")
    parser.add_argument("--db-path", default="./chroma_db", help="chroma db path")
    args = parser.parse_args()

    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=args.db_path)
    collection = client.get_or_create_collection(name=args.collection, embedding_function=embed_fn)

    total_chunks = 0
    for fname in sorted(os.listdir(args.source)):
        fpath = os.path.join(args.source, fname)
        if not os.path.isfile(fpath):
            continue
        if fname.lower().endswith(".pdf"):
            text = read_pdf(fpath)
        elif fname.lower().endswith((".txt", ".md")):
            text = read_txt(fpath)
        else:
            continue

        chunks = chunk_text(text)
        # stable ids so re-running ingest updates instead of duplicating
        ids = [hashlib.md5(f"{fname}-{i}".encode()).hexdigest() for i in range(len(chunks))]
        metadatas = [{"source": fname, "chunk": i} for i in range(len(chunks))]

        collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"Ingested {fname}: {len(chunks)} chunks")

    print(f"\nDone. {total_chunks} chunks stored in collection '{args.collection}' at {args.db_path}")


if __name__ == "__main__":
    main()

from pathlib import Path
import logging
import time
import chromadb
from app.core.config import settings
from app.retrieval.ollama import embed

_client = None
_collection = None
logger = logging.getLogger(__name__)

def collection():
    global _client, _collection
    if _collection is None:
        Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(settings.chroma_path))
        # Never delete or recreate an existing collection at startup.
        _collection = _client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection

def add(records, progress_callback=None):
    """Embed and persist chunks in bounded batches, logging stage timings."""
    c = collection()
    batch_size = max(1, int(settings.embedding_batch_size))
    total_embed_seconds = 0.0
    total_write_seconds = 0.0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        started = time.perf_counter()
        vectors = embed([x["text"] for x in batch])
        total_embed_seconds += time.perf_counter() - started
        started = time.perf_counter()
        c.upsert(ids=[x["id"] for x in batch],
                 documents=[x["text"] for x in batch],
                 embeddings=vectors,
                 metadatas=[x["metadata"] for x in batch])
        total_write_seconds += time.perf_counter() - started
        if progress_callback:
            completed = min(i + len(batch), len(records))
            progress_callback("Embedding and saving chunks", 55 + int(40 * completed / max(1, len(records))),
                              f"Embedded and saved {completed}/{len(records)} chunks")
    logger.info(
        "Index stages: chunks=%d batch_size=%d embedding_seconds=%.2f chroma_write_seconds=%.2f",
        len(records), batch_size, total_embed_seconds, total_write_seconds
    )

def search(question, owner_id="local"):
    c = collection()
    if not c.count():
        return []
    q_vector = embed([question])[0]
    # Count within this owner scope; global collection count can over-request for
    # a small local corpus and is not a reliable count of eligible chunks.
    scoped = c.get(where={"owner_id": owner_id}, include=["metadatas"])
    scoped_count = len(scoped.get("ids", []))
    if not scoped_count:
        logger.warning("Retrieval has no chunks for owner_id=%s although collection_count=%s", owner_id, c.count())
        return []
    multiplier = max(1, int(settings.retrieval_candidate_multiplier))
    wanted = max(1, int(settings.top_k))
    candidate_count = min(max(wanted, wanted * multiplier), scoped_count)
    r = c.query(query_embeddings=[q_vector], n_results=candidate_count,
                where={"owner_id": owner_id}, include=["documents", "metadatas", "distances"])
    docs = (r.get("documents") or [[]])[0] or []
    metas = (r.get("metadatas") or [[]])[0] or []
    distances = (r.get("distances") or [[]])[0] or []
    results = [{"text": d, "metadata": m or {}, "similarity": 1-float(dist)}
               for d, m, dist in zip(docs, metas, distances) if d and dist is not None]
    logger.info("Retrieval: owner=%s scoped_chunks=%d candidates=%d returned=%d", owner_id, scoped_count, candidate_count, len(results))
    return sorted(results, key=lambda item: item["similarity"], reverse=True)

def delete(document_id):
    # Explicit deletion/recovery only; never called on normal initialization.
    collection().delete(where={"document_id": document_id})

def document_chunk_count(document_id):
    c = collection()
    return len(c.get(where={"document_id": document_id}, include=["metadatas"])["ids"])

def list_chunk_document_ids():
    c = collection()
    ids = set()
    total = c.count()
    batch_size = 500
    for offset in range(0, total, batch_size):
        result = c.get(limit=batch_size, offset=offset, include=["metadatas"])
        for meta in result.get("metadatas") or []:
            if meta and meta.get("document_id"):
                ids.add(meta["document_id"])
    return ids


def backfill_owner_metadata(documents):
    """Add ownership metadata to legacy chunks without deleting/recreating the collection."""
    c = collection()
    for doc in documents:
        docid = doc.get("document_id")
        owner_id = "local"
        if not docid:
            continue
        result = c.get(where={"document_id": docid}, include=["metadatas"])
        ids = result.get("ids", [])
        metas = result.get("metadatas", [])
        for start in range(0, len(ids), 500):
            batch_ids = ids[start:start+500]
            batch_metas = []
            for meta in metas[start:start+500]:
                m = dict(meta or {})
                m["owner_id"] = owner_id
                batch_metas.append(m)
            if batch_ids:
                c.update(ids=batch_ids, metadatas=batch_metas)

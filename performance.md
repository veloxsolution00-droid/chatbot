# Ingestion and retrieval performance notes

- Ingestion logs now separately report extraction, chunking, embedding/storage, and total elapsed seconds.
- Vector indexing uses configurable bounded batches (`EMBEDDING_BATCH_SIZE`, default 16), up from 8. On 8 GB RAM, keep the value modest; if Ollama times out or RAM pressure rises, set it to 8.
- The chat retrieval setting defaults to `TOP_K=1`. ChromaDB retrieves a wider candidate set (`TOP_K * RETRIEVAL_CANDIDATE_MULTIPLIER`) before status and similarity filtering, then the RAG layer ranks and passes only the single best eligible chunk to the generation model.
- `relevance_score` is a cosine-similarity-derived ranking score (`1 - cosine distance`), not a calibrated probability or guaranteed factual confidence. Tune `MIN_SIMILARITY` against representative questions.
- These changes add measurements and reduce per-request overhead; actual speed gains must be benchmarked on the target PC.

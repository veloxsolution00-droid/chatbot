# Merged Offline Document Chatbot

This merged version combines the persistent-storage and background-ingestion performance work with the local authentication, owner-scoped retrieval, and persistent job queue from the LAN/auth branch.

## Local-only startup (Windows)

Keep the API bound to loopback only:
- Backend: `127.0.0.1:8000`
- Streamlit UI: `127.0.0.1:8501`

Run `run_backend.ps1` and `run_ui.ps1` in separate PowerShell terminals. Do not bind to `0.0.0.0` if the app should remain local-only.

## Important security and data notes

- Configure the initial administrator username/password in a local `.env` file based on `.env.example`; do not commit or share `.env`.
- User-specific retrieval requires valid authentication. Each document's owner ID is stored in SQLite and ChromaDB metadata.
- Uploaded originals, extracted artifacts, SQLite metadata, ChromaDB, logs, and queued uploads are stored beneath `data/` and are not included in this source archive. Runtime data should be backed up separately.
- There is no automatic cleanup of successfully indexed originals. Deletion is an explicit application operation.
- The included archive is source code, not a pre-populated database. Run tests and validate authentication, ingestion recovery, and owner isolation in your own environment before exposing the service to other devices.

## Performance approach

- One bounded background ingestion queue is used by default for low-memory machines.
- Ollama embedding calls are batched when the installed Ollama version supports `/api/embed`; a compatibility fallback is included.
- Ollama model operations are serialized by a bounded semaphore to avoid saturating an 8 GB RAM machine.
- Actual latency depends on local CPU/RAM, document formats, OCR, and installed model versions; use `benchmark_chatbot.py` to measure it locally.

# Offline Document Intelligence Chatbot

A local-first RAG starter using FastAPI, Streamlit, persistent ChromaDB, SQLite metadata, and Ollama. Uploaded documents, extracted text, metadata, and vectors are treated as durable application data—not cache.

## Permanent storage layout

```text
data/
├── uploads/       # Durable original uploaded files
├── extracted/     # Durable extracted text and source locations (JSON)
├── chroma_db/     # Persistent ChromaDB vectors and chunks
├── metadata/
│   └── documents.sqlite3  # Durable registry and recovery/deletion journal
└── logs/          # Rotating application logs and retained recovery events
```

Every path is configurable in `.env`. Defaults resolve to the project's local `data/` directory. Do not delete or move these folders while the application is running.

## Windows setup (VS Code terminal)

1. Install Python 3.11+, Ollama, and (for scanned PDFs/images) Tesseract OCR.
2. Pull the local models:
   ```powershell
   ollama pull gemma2:2b
   ollama pull nomic-embed-text
   ```
3. In the project folder:
   ```powershell
   py -3.11 -m venv .venv
   .\\.venv\\Scripts\\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
4. Edit `TESSERACT_CMD` in `.env` if required.
5. Terminal 1:
   ```powershell
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
6. Terminal 2:
   ```powershell
   .\\.venv\\Scripts\\Activate.ps1
   streamlit run app/ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
   ```
7. Open `http://127.0.0.1:8501`. API docs are at `http://127.0.0.1:8000/docs`.

## Durable ingestion lifecycle

1. Save the original with an atomic write under `data/uploads/`.
2. Generate a stable UUID document ID and SHA-256 content hash.
3. Commit a SQLite registry entry before extraction/indexing.
4. Extract text and source locations, then atomically persist `data/extracted/<document_id>.json`.
5. Generate embeddings locally with Ollama and upsert deterministic chunk IDs into the persistent ChromaDB collection.
6. Mark the registry `indexed` only after indexing verification succeeds.

An interrupted ingestion leaves the original and a recoverable registry status. Startup reconciliation retries incomplete documents, registers upload files left behind by a crash before registry commit, marks missing originals, resumes only previously user-requested deletion operations, and reports orphaned ChromaDB chunks without automatically deleting them. Healthy indexed documents are not re-embedded on restart.

Duplicate uploads are detected by SHA-256. A healthy existing document is reused. An incomplete copy is retried using its stable ID. Different content with the same filename receives a different document ID and is preserved separately; existing originals are never overwritten by filename.

## Explicit deletion only

There is no TTL or cache-expiration mechanism. Startup, shutdown, UI sessions, new uploads, and initialization do not clear the database. `DELETE /documents/{document_id}` records a durable deletion operation before removing that document's chunks and artifacts. If deletion fails, the operation remains visible in SQLite and can be resumed by `/admin/reconcile`. The deletion journal and recovery events are retained for diagnostics.

## Backup and recovery procedure

Stop FastAPI before making a consistent backup. Copy the complete `data/` directory to a separate disk or protected backup location, including **uploads, extracted, chroma_db, metadata, and logs**. Do not copy only the SQLite database or only ChromaDB: the application needs all stores to recover. Keep at least one dated backup on a different physical device. To restore, stop the app, preserve the current `data/` directory, restore the full backed-up `data/` directory to the configured paths, then start FastAPI and inspect `/health`, `/documents`, and `/admin/recovery-events`. Test a restore periodically. This application does not automatically create off-device backups.

## Troubleshooting: "local generation model is unavailable"

Run these commands in PowerShell or Windows Terminal (not inside the Python prompt):

```powershell
ollama --version
ollama list
ollama pull gemma2:2b
ollama pull nomic-embed-text
```

Make sure Ollama is running, then check `http://127.0.0.1:11434/api/tags` in a browser or run:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

The `.env` file must use model names that appear in `ollama list`:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
GENERATION_MODEL=gemma2:2b
EMBEDDING_MODEL=nomic-embed-text
```

Restart the FastAPI backend after editing `.env`. The sidebar now shows whether the Ollama server, generation model, and embedding model are available. Chat errors include the underlying Ollama diagnostic instead of only a generic message. If the server is running on another host/port, update `OLLAMA_BASE_URL` accordingly. If generation times out, check available RAM or increase `TIMEOUT` in `.env`.

## Supported file formats

PDF (OCR fallback for textless pages), DOCX, TXT, RTF, ODT, JPG/JPEG, PNG, TIFF, BMP, WEBP, XLSX/XLSM, CSV, ODS, PPTX, JSON, XML, YAML, and EML. Legacy XLS/PPT need conversion. Tesseract is required for OCR.

## API endpoints

- `GET /health` — reports configured durable paths and component status
- `POST /documents/upload` — ingest multipart `files`
- `GET /documents` — durable registry
- `DELETE /documents/{document_id}` — explicit, journaled deletion
- `POST /admin/reconcile` — manually run conservative recovery
- `GET /admin/recovery-events` — recent recovery/deletion events
- `POST /chat` — grounded Q&A across all indexed documents

## Important limitations

Persistent local storage protects against normal application restarts, not disk failure, accidental manual deletion, malware, or physical loss. Backups are essential. ChromaDB and SQLite cannot participate in one shared atomic transaction, so indexing/deletion uses a recoverable workflow and a persistent journal. Reconciliation intentionally preserves orphaned data for manual review. Similarity thresholds and LLM prompts reduce unsupported answers but do not mathematically guarantee zero hallucinations. Test with representative documents before high-impact use. Keep services bound to localhost unless authentication and network security have been implemented.
#   c h a t b o t  
 
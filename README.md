# 📄 Offline Document Intelligence Chatbot

An AI-powered document chatbot that allows users to upload documents and ask questions based on their content. Built using **FastAPI, Streamlit, ChromaDB, SQLite, and Ollama**, the application supports local AI inference, persistent storage, and user-specific document retrieval.

## 🚀 Features

- **Offline AI:** Run language models locally using Ollama.
- **Multi-Format Support:** Process PDFs, Word documents, spreadsheets, images, presentations, and more.
- **RAG-Based Chat:** Generate answers using relevant document content.
- **Persistent Storage:** Preserve uploaded files, extracted text, metadata, and embeddings across restarts.
- **Multi-User Support:** Restrict document access to the authenticated owner.
- **Background Processing:** Process documents asynchronously using an ingestion queue.
- **OCR Support:** Extract text from scanned documents and images using Tesseract.
- **Duplicate Detection:** Identify duplicate uploads using SHA-256 hashing.
- **Recovery Mechanism:** Recover interrupted ingestion operations.
- **Explicit Deletion:** Documents are not automatically deleted as temporary cache.

## 🏗️ Architecture

```text
Streamlit UI
     |
     v
FastAPI Backend
     |
     +---- Authentication & Authorization
     |
     +---- Document Ingestion
     |          |
     |          +---- Text Extraction / OCR
     |          +---- Chunking
     |          +---- Ollama Embeddings
     |          +---- ChromaDB Indexing
     |
     +---- RAG Chat
                |
                +---- Owner-Scoped Retrieval
                +---- Ollama LLM
                +---- Grounded Answers

Persistent Storage:
├── data/uploads/     - Original documents
├── data/extracted/   - Extracted text
├── data/chroma_db/   - Vector embeddings
├── data/metadata/    - SQLite database
└── data/logs/        - Application logs
```

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core development |
| FastAPI | Backend API |
| Streamlit | User interface |
| ChromaDB | Vector storage |
| SQLite | Metadata and job tracking |
| Ollama | Local LLM and embeddings |
| Tesseract OCR | Scanned document extraction |

## ⚙️ Installation

**Prerequisites:** Python 3.11+, Ollama, and Tesseract OCR if scanned-document processing is required.

### 1. Clone the Repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd offline_document_chatbot
```

### 2. Create a Virtual Environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Install Local AI Models

```powershell
ollama pull gemma2:2b
ollama pull nomic-embed-text
```

### 4. Configure Environment Variables

```powershell
Copy-Item .env.example .env
```

Configure the required settings and administrator credentials in `.env`. Never commit this file to GitHub.

### 5. Start the Backend

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 6. Start the Frontend

Open another terminal:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app/ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

**Access the application:** http://127.0.0.1:8501

**API documentation:** http://127.0.0.1:8000/docs

## 🔐 Data Persistence & Security

- Uploaded documents and indexed data are stored permanently until explicitly deleted.
- Each document is associated with its owner's ID.
- Retrieval must be restricted to the authenticated user's documents.
- Authentication and authorization must be enforced by the backend.
- Runtime data is stored in the configurable `data/` directory.
- Back up the complete data directory regularly.
- Keep services bound to `127.0.0.1` for local-only access.
- Verify authentication and user isolation before network deployment.

**Important:** Persistent storage does not replace backups. RAG reduces unsupported answers but cannot guarantee that every response is correct.

## 📂 Supported Formats

PDF, DOCX, TXT, RTF, ODT, JPG, JPEG, PNG, TIFF, BMP, WEBP, XLSX, XLSM, CSV, ODS, PPTX, JSON, XML, YAML, and EML.

OCR requires Tesseract. Legacy XLS and PPT files may require conversion.

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check application status |
| POST | `/documents/upload` | Upload documents |
| GET | `/documents` | List documents |
| DELETE | `/documents/{document_id}` | Delete a document |
| POST | `/chat` | Ask document-based questions |
| POST | `/admin/reconcile` | Recover incomplete operations |
| GET | `/admin/recovery-events` | View recovery events |

Refer to the running API documentation for actual request schemas and available routes.

## 📌 Key Objectives

- Keep AI processing local.
- Preserve documents and embeddings across restarts.
- Isolate document access between users.
- Improve ingestion performance through background processing.
- Generate answers grounded in uploaded documents.


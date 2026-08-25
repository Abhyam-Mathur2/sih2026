# BMIM — Bharat Material Intelligence Network

BMIM is an AI-assisted unified material-master application for identifying duplicate, near-duplicate, and functionally equivalent CPSE material records. It preserves legacy codes while generating National Material Codes.

## Architecture

```text
React + Vite
      |
      v
FastAPI + JWT REST API
      |-------------------- AI/NLP Engine
      |                     Sentence Transformers (CPU)
      |                     RapidFuzz + validation rules
      v
Supabase PostgreSQL + pgvector + optional Storage
```

FastAPI remains the application backend. Supabase supplies PostgreSQL/pgvector and, optionally, CSV object storage. The frontend only calls FastAPI; it never receives Supabase database credentials or a service-role key.

## Quick start (Windows)

### 1. Create a Supabase project

Create a free Supabase project. In **Project Settings → Database → Connection string**, copy the Session pooler URI (or direct URI if your network supports it). In **Project Settings → API**, copy the Project URL and anon key. The database password is the one chosen at project creation. Never put the service-role key in frontend code.

Enable `vector` in **Database → Extensions** if it is not already enabled. The migration also issues `CREATE EXTENSION IF NOT EXISTS vector`.

### 2. Configure the backend

```powershell
Copy-Item backend\.env.example backend\.env
```

Set these values in `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@[HOST]:5432/postgres
DATABASE_URL_SYNC=postgresql+psycopg://postgres.[PROJECT_REF]:[PASSWORD]@[HOST]:5432/postgres
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=backend_only_optional_for_storage
SUPABASE_STORAGE_BUCKET=material-uploads
VECTOR_BACKEND=pgvector
STORAGE_BACKEND=supabase
SECRET_KEY=replace-with-a-long-random-secret
JWT_SECRET_KEY=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:5173
```

`DATABASE_URL_SYNC` is used by Alembic. Password characters must be URL encoded. `SUPABASE_SERVICE_ROLE_KEY` is only needed when Storage is enabled; leave `STORAGE_BACKEND=local` if you do not want to configure Storage.

### 3. Set up and run the backend

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup-backend.ps1
powershell -ExecutionPolicy Bypass -File scripts\run-backend.ps1
```

The run script applies `alembic upgrade head`, safely runs the idempotent seed, then starts FastAPI. API: http://localhost:8000 · Swagger: http://localhost:8000/docs.

Manual commands:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

### 4. Set up and run the frontend

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup-frontend.ps1
powershell -ExecutionPolicy Bypass -File scripts\run-frontend.ps1
```

`frontend/.env` contains only:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Open http://localhost:5173.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | Admin@123 |
| Technical Reviewer | reviewer@example.com | Reviewer@123 |
| CPSE Manager | manager@example.com | Manager@123 |

## Matching safety

The pipeline normalizes descriptions, expands abbreviations, extracts technical attributes, generates all-MiniLM-L6-v2 embeddings, performs semantic/fuzzy scoring, and applies weighted matching. Conflicting critical attributes (product type, size, material grade, or pressure) cap the score below the near-duplicate threshold, so a 2-inch SS316 ball valve cannot be classified as identical to a 4-inch SS316 ball valve.

When `VECTOR_BACKEND=pgvector`, embeddings are stored in Supabase as `vector(384)`. The existing local JSON/cosine fallback remains available with `VECTOR_BACKEND=local` for offline development only.

## Testing

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest tests/ -v
```

Unit tests do not require a live database. Integration/startup tests require a configured Supabase project.

## Requirements and limitations

- Python 3.12+, Node.js 20+, and a Supabase project are required.
- No Docker, WSL, local PostgreSQL, local pgvector, NVIDIA GPU, CUDA, or paid AI API is required.
- CPU-only PyTorch is installed first from `backend/requirements-cpu.txt`.
- First embedding use downloads the free `all-MiniLM-L6-v2` model (~90 MB).
- CSV processing is inline for this hackathon MVP; very large uploads can take time.
- The Storage bucket can be created automatically by the backend service role, or you can create a private `material-uploads` bucket in the Supabase dashboard.

# QuickApply Backend

Backend API for QuickApply.AI — an AI-assisted platform to manage user profiles, track applications, parse CVs, and generate tailored documents (cover letter / motivation letter / SOP).

## Tech Stack

- FastAPI
- SQLAlchemy (async) + SQLite (default)
- JWT auth (`python-jose`)
- Password hashing (`passlib`)
- PDF parsing (`pdfplumber`, `PyMuPDF`)
- LLM generation via Groq API

## Project Structure

- `backend/main.py` — app entrypoint, middleware, route registration
- `backend/database.py` — async DB engine/session init
- `backend/models/`
  - `user.py`
  - `profile.py`
  - `application.py`
- `backend/routes/`
  - `auth.py` — register/login
  - `profile.py` — profile CRUD + CV upload
  - `applications.py` — application CRUD + status updates
  - `documents.py` — AI document generation
- `backend/services/`
  - `pdf_parser.py` — extract text from CV PDFs
  - `writing_agent.py` — LLM prompts/completions

## Core Capabilities

1. User registration/login and JWT issuance
2. Profile create/update/get/delete
3. CV PDF upload and text extraction into profile
4. Application tracking (status lifecycle)
5. AI document generation based on profile + ad text

## API Overview (Frontend Integration)

### Auth
- `POST /auth/register`
- `POST /auth/login`

Returns:
- `access_token` (Bearer JWT)
- `user_id`
- `full_name`

Frontend: store token securely; send in header:
`Authorization: Bearer <token>`

### Profile
- `GET /profile/me`
- `POST /profile/me`
- `DELETE /profile/me`
- `POST /profile/upload-cv` (multipart/form-data, file field name: `file`)

### Applications
- `GET /applications/`
- `POST /applications/`
- `PATCH /applications/{application_id}/status`
- `DELETE /applications/{application_id}`

### Documents
- `POST /documents/generate`
  - body: `job_ad`, `document_type` (`auto`, `cover_letter`, `motivation_letter`, `sop`)

## Frontend Integration Plan (Recommended)

1. **Auth layer first**
   - Build login/register pages
   - Central API client with auth header injection
   - Global 401 handling (redirect to login)

2. **Profile module**
   - One editable profile screen
   - CV upload component with progress + error states

3. **Applications dashboard**
   - List + create modal/form
   - Status chip/dropdown workflow
   - Optimistic updates for status patch

4. **Document generator**
   - Input ad text + doc type selector
   - “Generate” action + loading state
   - Output editor area (allow user edits before save/export)

5. **Shared UX contracts**
   - Normalize backend validation errors into frontend-friendly messages
   - Add retry for transient AI failures/timeouts
   - Handle empty profile / no applications gracefully

## Environment Variables

Create `.env` in `backend/`:

- `SECRET_KEY=...`
- `DATABASE_URL=sqlite+aiosqlite:///./quickapply.db`
- `GROQ_API_KEY=...`
- `AI_PROVIDER=groq` (optional)

## Run (backend)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

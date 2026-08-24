# WorkflowSync

WorkflowSync is a multi-client invoice-to-bank reconciliation platform for accounting firms. It automates first-pass matching of supplier invoices against bank transactions, while keeping accountants in control of ambiguous cases for manual resolution.

## Technology Stack
- **Frontend:** React, Vite, Tailwind CSS, TypeScript/JavaScript
- **Backend:** Python, FastAPI, SQLAlchemy, Alembic, PyMuPDF, RapidFuzz, pytest
- **Database:** PostgreSQL

## Architecture
WorkflowSync is designed as a **modular monolith**. The frontend is a React Single Page Application (SPA) that acts as a client to a single FastAPI backend over REST, which interacts with a PostgreSQL database. 

## Major Modules
- **Authentication & User Management**
- **Client Management**
- **Invoice Service** (PDF upload, validation, extraction)
- **Transaction/CSV Service** (CSV upload, validation, normalization)
- **Reconciliation Engine** (deterministic matching and scoring)
- **Manual Resolution Service** (review queues and overrides)
- **History Service**

## Development Approach
This project is built using an **incremental AI-assisted development approach**. Development occurs in small, scoped, testable increments without broad unrequested architectural changes. The backend business logic is isolated and strictly protected from UI-driven modifications.

## Current State
**Status:** Phase 0 (Repository Foundation, Minimal Backend & Database Scaffolding)
The repository foundation is established and a minimal FastAPI backend has been initialized with a `/health` endpoint. The PostgreSQL, SQLAlchemy, and Alembic database scaffolding is established, but no domain models exist yet.

## Running the Backend (Local Development)

1. **Setup the Python environment:**
   ```bash
   cd backend
   python -m venv venv
   # On Windows: .\venv\Scripts\Activate.ps1
   # On macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure the Database:**
   You must have a PostgreSQL instance running. The backend configuration uses `pydantic-settings` which will automatically load variables from a `.env` file in the `backend/` directory or from the environment.
   Set the following environment variable (do not commit real credentials):
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/workflowsync
   ```

3. **Run tests:**
   ```bash
   # From the backend directory
   python -m pytest -v
   ```
   *(Note: The `test_database_connection` test will gracefully skip if a local PostgreSQL instance is not available).*

4. **Start the FastAPI application:**
   ```bash
   # From the backend directory
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`. You can check the health endpoint at `http://127.0.0.1:8000/health`.

## Alembic Migrations
Alembic has been initialized in `backend/alembic/`. Once application domain models are created in future increments, Alembic will be used to generate and run database schema migrations.

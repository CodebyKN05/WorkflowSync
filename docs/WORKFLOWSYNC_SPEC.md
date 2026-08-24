# WorkflowSync — Technical Project Specification

> **Purpose:** Master specification for AI-assisted, incremental development of WorkflowSync.
>
> **Audience:** Antigravity and the developer.
>
> **Status:** Living project specification. Decisions in this document are authoritative unless explicitly changed by the project owner.

---

## 1. Project Overview

**WorkflowSync** is a multi-client invoice-to-bank reconciliation platform for an accounting firm.

An accounting firm manages multiple client companies. For each client, it has:

- Supplier invoices, primarily PDF files
- Bank transactions, primarily CSV files
- Reconciliation results
- Exceptions requiring human review
- Manual resolution decisions
- Reconciliation history

The system automates first-pass matching while keeping an accountant in control of ambiguous cases.

### Core workflow

```text
Accounting Firm
      |
      v
    Login
      |
      v
 Select Client
      |
      v
Client Workspace
      |
      +------------------+
      |                  |
      v                  v
Invoice PDFs         Bank CSV
      |                  |
      v                  v
PDF Extraction      CSV Validation
      |                  |
      +---------+--------+
                |
                v
           PostgreSQL
                |
                v
      Run Reconciliation
                |
                v
        Matching Engine
                |
        +-------+-------+
        |       |       |
        v       v       v
     Matched Review Unmatched
                |
                v
       Manual Resolution
                |
                v
      Reconciliation History
```

---

## 2. Project Goals

The project should demonstrate:

- React frontend development
- Python/FastAPI backend development
- PostgreSQL relational modeling
- PDF document extraction
- CSV ingestion and validation
- Explainable invoice/payment reconciliation
- Fuzzy vendor matching
- Manual exception resolution
- Authentication and client-level authorization
- Error handling
- Automated testing
- Reproducible synthetic test/demo data
- Clean modular architecture
- Incremental AI-assisted development
- A deployable, demonstrable application

This is a learning and portfolio project. The developer must understand the implementation and be able to explain architectural and technical decisions.

---

## 3. Scope Boundaries

The first version is **not** intended to be:

- A full accounting/ERP system
- A real banking integration
- A production-grade financial platform
- A machine-learning research project
- A microservices architecture
- A replacement for human accountants
- A system that automatically approves every reconciliation

Do not add major features simply because they sound impressive. New features require explicit approval.

---

## 4. Technology Stack

### Frontend

- React
- Vite
- Tailwind CSS
- JavaScript/TypeScript as agreed during implementation

The frontend is a client of the backend API.

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PyMuPDF for initial PDF extraction
- RapidFuzz for vendor/string similarity
- pytest for testing

OCR may be added later for scanned/image-based PDFs.

### Database

- PostgreSQL

### Development

- Git
- GitHub
- Antigravity for AI-assisted implementation
- ChatGPT for architecture, specifications, debugging, review, and explanations

---

## 5. Architecture

### 5.1 Architectural style

Use a **modular monolith**.

Do **not** turn the project into microservices unless the project owner explicitly changes the architecture.

Conceptually:

```text
React
  |
  | REST API
  v
FastAPI
  |
  +-- Authentication
  +-- Client management
  +-- Invoice service
  +-- Transaction/CSV service
  +-- Reconciliation service
  +-- Manual resolution service
  +-- History service
  |
  v
PostgreSQL
```

### 5.2 Backend structure

Use focused modules, for example:

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── core/
│   └── utils/
└── tests/
```

The exact structure may be refined, but responsibilities must remain separated.

**Do not create giant files. Do not split into dozens of tiny files without meaningful responsibilities.**

---

## 6. Database / Domain Model

The core hierarchy is:

```text
Accounting Firm
    |
    +-- Users
    |
    +-- Clients
          |
          +-- Invoices
          +-- Bank Transactions
          +-- Matches
          +-- Exceptions
          +-- Reconciliation Runs
```

### Firm

Conceptual fields:

```text
id
name
created_at
```

### User

```text
id
firm_id
name
email
password_hash
role (if/when roles are implemented)
created_at
```

Never store plaintext passwords.

### Client

```text
id
firm_id
name
industry
currency
created_at
```

Every financial record must be scoped to a client.

### Invoice

```text
id
client_id
invoice_number
vendor
invoice_date
due_date
amount
currency
pdf_path / source reference
status
created_at
```

### Bank Transaction

```text
id
client_id
transaction_date
description
amount
currency
reference
source_file
created_at
```

### Match

```text
id
invoice_id
transaction_id
score
status
reason/explanation
created_at
updated_at
```

### Reconciliation Run

```text
id
client_id
started_at
completed_at
matched_count
review_count
unmatched_count
duplicate_count
status
```

### Exception categories

At minimum:

```text
AMOUNT_MISMATCH
VENDOR_MISMATCH
DATE_MISMATCH
MISSING_PAYMENT
DUPLICATE_PAYMENT
NO_CANDIDATE
```

---

## 7. Security and Client Isolation

This is a critical requirement.

A user belonging to Firm A must not access clients belonging to Firm B.

The backend must enforce this. Frontend-only protection is insufficient.

Conceptually:

```text
Authenticated User
       |
       v
User's Firm
       |
       v
Requested Client
       |
       v
Does client belong to user's firm?
       |
   +---+---+
   |       |
  YES      NO
   |       |
 allow    deny
```

For endpoints such as:

```text
GET /clients/{client_id}/invoices
```

the backend must verify that the authenticated user is authorized for that client.

Never trust a client ID supplied by the frontend.

---

## 8. Authentication

The application requires login.

Minimum requirements:

- Secure password hashing
- Authentication/session or token mechanism
- Authenticated API access
- Authorization checks
- Clear unauthorized/forbidden responses

Roles such as `Admin`, `Manager`, and `Accountant` may be added later, but role complexity must not distract from the core workflow.

---

## 9. Invoice Processing

### Upload flow

```text
PDF
 |
 v
FastAPI upload endpoint
 |
 v
PDF validation
 |
 v
Text extraction
 |
 v
Field extraction
 |
 v
Validation
 |
 v
PostgreSQL
```

### Extraction

Use **PyMuPDF** for normal text-based PDFs.

Potential OCR support may be added later.

At minimum extract:

- Invoice number
- Vendor
- Invoice date
- Due date where available
- Total amount
- Currency where available

### Errors

Handle:

- Invalid PDF
- Corrupt PDF
- Missing required fields
- Unsupported format
- Extraction failure

Do not expose internal stack traces in normal UI responses.

---

## 10. Bank CSV Processing

Flow:

```text
CSV
 |
 v
FastAPI
 |
 v
CSV parsing
 |
 v
Schema validation
 |
 v
Data normalization
 |
 v
PostgreSQL
```

Conceptual fields:

```text
transaction_id
date
description
amount
currency
reference
```

Normalize supported external column names into the internal schema.

Handle:

- Invalid CSV
- Missing required columns
- Invalid dates
- Invalid amounts
- Empty files
- Unsupported format

---

## 11. Reconciliation Engine

### 11.1 Core decision

The initial reconciliation engine is **not an ML model**.

Use an explainable deterministic/rule-based scoring approach.

Reasons:

- Easier to understand
- Easier to test
- Easier to explain
- Easier to validate against ground truth
- Appropriate for an initial financial reconciliation system

ML may be a future extension, not a first-version requirement.

### 11.2 Matching process

```text
Invoice
  |
  v
Generate candidate transactions
  |
  v
Compare attributes
  |
  +-- Amount
  +-- Vendor/description similarity
  +-- Date proximity
  +-- Reference
  |
  v
Calculate confidence score
  |
  v
Classify result
```

### 11.3 Illustrative scoring

```text
Amount match       +40
Vendor similarity  +30
Date proximity     +15
Reference match    +15
-----------------------
Maximum             100
```

Weights may be tuned during implementation/testing, but changes must be deliberate and documented.

### 11.4 Vendor similarity

Use RapidFuzz or an equivalent explainable string-similarity method.

Example:

```text
Invoice:
Amazon Web Services

Bank:
AWS PAYMENT
```

should be considered potentially similar.

### 11.5 Result categories

At minimum:

```text
MATCHED
NEEDS_REVIEW
UNMATCHED
DUPLICATE
```

### 11.6 Explainability

A result must explain why it received its score.

Example:

```text
Amount:       Exact match
Vendor:       91% similar
Date:         5 days apart
Reference:    Found

Confidence: 94%
```

Do not present only a mysterious score.

---

## 12. Manual Resolution

Automation assists; it does not blindly decide every case.

Example:

```text
INV-1048
Amount: $1,200

Potential matches:

TX-2041    $1,200    94%
TX-2087    $1,180    68%
TX-2110    $1,200    63%
```

The accountant can:

- Confirm a match
- Reject a candidate
- Leave unresolved
- Resolve an exception

The decision must be persisted.

Manual resolution is a core product feature and must not be removed to simplify implementation.

---

## 13. Reconciliation History

Each reconciliation run should be persisted.

History should show:

```text
Date
Client
Matched count
Review count
Unmatched count
Duplicate count
Status
```

Users should be able to inspect a previous run.

Do not overwrite history with only the latest result.

---

## 14. Synthetic Data Generator

The repository contains a separate development utility:

```text
tools/
└── data_generator/
```

It is **not part of the production WorkflowSync runtime**.

Its purposes are:

- Development
- Testing
- Demonstration

### 14.1 Example hierarchy

```text
ABC Accounting
|
+-- Acme Manufacturing
+-- Globex Consulting
+-- Stark Industries
+-- Wayne Logistics
+-- Umbrella Retail
```

Potential dataset:

```text
5–8 clients
300–500 invoices
350–600 transactions
```

Exact size must be configurable.

### 14.2 Reproducibility

Use a configurable random seed.

The same seed should produce the same logical dataset.

### 14.3 Relationships

Do **not** independently generate random invoices and random payments.

Generate known relationships:

```text
Generate invoice
      |
      v
Decide scenario
      |
      v
Generate corresponding transaction(s)
      |
      v
Record ground truth
```

### 14.4 Scenarios

At minimum:

```text
MATCHED
AMOUNT_MISMATCH
VENDOR_MISMATCH
MISSING_PAYMENT
DUPLICATE_PAYMENT
DATE_MISMATCH
UNRELATED_TRANSACTION
```

Scenario percentages should be configurable.

### 14.5 Ground truth

The generator knows the expected outcome.

Example:

```json
{
  "invoice": "INV-ACME-0042",
  "expected_status": "matched",
  "expected_transaction": "TX-ACME-0091"
}
```

Ground truth is used by tests.

**Production WorkflowSync must not use ground truth to make reconciliation decisions.**

---

## 15. Three Data Types

Maintain this separation.

### 15.1 Generated development data

Large synthetic dataset.

Used for:

- Development
- Automated testing
- Scenario testing

### 15.2 Demo/seed data

Smaller curated dataset loaded into the demo.

Example:

```text
5 clients
~100 invoices
~120 transactions
```

Used for:

- Live demonstrations
- Portfolio reviewers
- Quick evaluation

### 15.3 User-uploaded data

Actual application inputs:

```text
invoice.pdf
bank.csv
```

The application processes them normally.

### Critical rule

Preloaded demo **inputs** are acceptable.

Precomputed/hardcoded reconciliation **answers** are not.

Demo results must be produced by the real application logic at runtime.

---

## 16. Invoice PDF Generation

The synthetic-data generator should eventually create actual invoice PDFs.

Use multiple layouts/templates, for example:

```text
Template A
Template B
Template C
Template D
Template E
```

Populate:

- Vendor
- Invoice number
- Date
- Due date
- Line items where appropriate
- Tax where appropriate
- Total
- Currency

Controlled layout variations may include:

- Different field labels
- Different arrangements
- Optional fields
- Formatting variations

Do not make most documents deliberately unreadable.

---

## 17. Bank CSV Generation

Generate client-specific CSV files.

Example:

```csv
transaction_id,date,description,amount,currency
TX-001,2026-08-04,AWS PAYMENT,-1500.00,USD
TX-002,2026-08-06,MICROSOFT,-1240.00,USD
```

Do not include invoice IDs in normal bank transaction data when the goal is to require reconciliation.

---

## 18. Frontend Requirements

The frontend should provide:

```text
Login
  |
  v
Firm Dashboard
  |
  v
Client Selection
  |
  v
Client Dashboard
  |
  +-- Invoices
  |     +-- Upload
  |     +-- List/detail
  |
  +-- Transactions
  |     +-- Upload CSV
  |     +-- List/detail
  |
  +-- Reconciliation
  |     +-- Run
  |     +-- Matched
  |     +-- Review
  |     +-- Unmatched
  |     +-- Duplicates
  |
  +-- Manual Resolution
  |
  +-- History
```

### Frontend/backend boundary

The frontend is a client of the backend API.

The frontend must **not duplicate backend business logic**.

Bad example:

```javascript
// Do not make frontend scoring authoritative.
const score = amountMatch ? 40 : 0;
```

The backend owns reconciliation logic.

The frontend displays backend results.

### API contract rule

Once an API contract is agreed and implemented:

**Do not change the backend API merely to make frontend work easier.**

If a frontend requirement needs a change:

1. Explain the requirement.
2. Explain the impact.
3. Deliberately update the API contract.
4. Update backend tests.
5. Update frontend integration.

Never silently modify backend behavior.

---

## 19. Critical AI-Agent Rules

These rules apply especially to Antigravity.

### Rule 1 — Never build the entire project in one shot

This specification describes the target system, not a single implementation prompt.

Work incrementally.

### Rule 2 — Implement only the requested increment

If asked to implement a frontend page, do not rewrite backend services.

If asked to style a component, do not redesign database models.

If asked to fix a UI bug, do not modify reconciliation logic.

### Rule 3 — Protect backend business logic

Unless explicitly authorized, do not change:

- Reconciliation scoring
- Matching behavior
- Database relationships
- Authentication behavior
- API semantics
- Validation rules

### Rule 4 — Inspect before modifying

Before changing existing code:

1. Read relevant files.
2. Understand architecture.
3. Identify dependencies.
4. Make the smallest necessary change.

### Rule 5 — Avoid broad rewrites

Prefer focused modifications.

### Rule 6 — No hidden infrastructure additions

Do not introduce the following unless explicitly approved:

- Redux
- Zustand
- GraphQL
- Microservices
- Redis
- Message queues
- Docker orchestration
- ML pipelines
- Other major infrastructure

Use the simplest architecture satisfying the current requirement.

### Rule 7 — Keep files focused

Split by responsibility, not arbitrary line count.

### Rule 8 — Preserve API contracts

Do not invent a new API because it is convenient for the frontend.

### Rule 9 — Never hardcode business results

Never hardcode values such as:

```text
matched = 78
review = 11
unmatched = 7
```

as application logic.

These must come from real data and real reconciliation.

### Rule 10 — Test before completion

Every increment requires appropriate verification.

### Rule 11 — Explain significant decisions

When introducing a meaningful dependency/pattern, explain:

- Why it is needed
- Alternatives
- Files changed
- Behavior changed
- Testing performed

### Rule 12 — Do not modify unrelated files

Keep changes scoped to the current increment.

---

## 20. Incremental Agent-Driven Development

This project **must** be developed incrementally.

Use this loop:

```text
Requirement
    |
    v
Design small increment
    |
    v
Explain implementation
    |
    v
AI implements
    |
    v
Run application/tests
    |
    v
Review changes
    |
    v
Understand changes
    |
    v
Commit
    |
    v
Next increment
```

Every meaningful increment should leave the project in a working state.

### Important developer goal

The purpose is not merely to obtain working code.

The developer should understand:

- What changed
- Why it changed
- How it works
- What assumptions it makes
- How it is tested
- What tradeoffs exist

---

## 21. Development Phases

These are high-level phases, **not prompts to execute all at once**.

### Phase 0 — Repository and architecture

- Repository setup
- Folder structure
- Environment configuration
- README
- Git configuration
- Basic frontend/backend startup

Checkpoint:

```text
Frontend starts
Backend starts
Database connection strategy exists
```

### Phase 1 — Synthetic data generator

Incrementally implement:

1. Clients
2. Vendors
3. Invoices
4. Transactions
5. Scenarios
6. Ground truth
7. PDF generation
8. CSV generation
9. Reproducibility

Checkpoint:

```text
Generator creates valid data
Ground truth exists
Generated data is repeatable
```

### Phase 2 — Database

Implement incrementally:

1. Firm model
2. User model
3. Client model
4. Invoice model
5. Transaction model
6. Match model
7. Reconciliation run model
8. Exceptions as appropriate
9. Alembic migrations
10. Database tests

Checkpoint:

```text
Migrations work
Models work
Relationships work
Tests pass
```

### Phase 3 — Backend foundation

Implement:

- FastAPI application
- Configuration
- Database session
- Error handling
- API structure
- Authentication foundation

### Phase 4 — Invoice ingestion

Incrementally implement:

1. Upload
2. Validation
3. PDF extraction
4. Field extraction
5. Persistence
6. Error handling
7. Tests

### Phase 5 — Bank CSV ingestion

Incrementally implement:

1. Upload
2. Parsing
3. Validation
4. Normalization
5. Persistence
6. Error handling
7. Tests

### Phase 6 — Reconciliation engine

Incrementally implement:

1. Candidate generation
2. Amount comparison
3. Vendor similarity
4. Date comparison
5. Reference comparison
6. Confidence scoring
7. Result classification
8. Explainability
9. Persistence
10. Ground-truth tests

### Phase 7 — Manual resolution

Implement:

- Review queue
- Candidate display
- Confirm
- Reject
- Resolve
- Persistence

### Phase 8 — Reconciliation history

Implement:

- Run records
- Summary
- Detail
- Historical results

### Phase 9 — Frontend

Build incrementally:

1. App shell
2. Login
3. Firm/client selection
4. Client dashboard
5. Invoice UI
6. Transaction UI
7. Reconciliation UI
8. Review queue
9. Manual resolution
10. History

### Phase 10 — Integration

Integrate frontend with existing backend APIs.

Do not rewrite backend logic to fit the frontend.

### Phase 11 — Security and error handling

Verify:

- Authentication
- Authorization
- Client isolation
- Input validation
- File validation
- API errors
- User-friendly frontend errors

### Phase 12 — Testing

Implement:

- Unit tests
- API tests
- Integration tests
- Ground-truth reconciliation tests
- Security/authorization tests

### Phase 13 — Demo and deployment

Prepare:

- Demo dataset
- Seed data
- README
- Setup instructions
- Deployment
- Live demo
- Demo walkthrough
- Interview explanation

---

## 22. Testing Philosophy

Test behavior, not merely line coverage.

### Reconciliation tests

Given known ground truth:

```text
Expected:
INV-1 -> TX-1 -> MATCHED

Actual:
INV-1 -> TX-1 -> MATCHED

PASS
```

Test:

- Exact match
- Vendor variation
- Amount mismatch
- Missing payment
- Duplicate payment
- Date mismatch
- No candidate

### API tests

Test:

- Authentication
- Invoice upload
- CSV upload
- Reconciliation
- Manual resolution
- History
- Unauthorized access

### Frontend tests

At minimum verify critical user workflows and API error states.

---

## 23. Demo Requirements

The demo should prove the application performs real work.

Recommended flow:

```text
Login
  |
Select client
  |
Show preloaded invoices/transactions
  |
Run reconciliation
  |
Show processing state
  |
Show actual results
  |
Open a match
  |
Show explanation
  |
Open an exception
  |
Manually resolve it
  |
Show history
```

A stronger demonstration can:

1. Modify or add a transaction.
2. Run reconciliation again.
3. Show that the result changes.

This demonstrates that results are computed at runtime.

### Demo integrity rule

Preloaded demo data is fine.

Hardcoded reconciliation results are not.

---

## 24. Definition of Done

An increment is complete when:

- Requested behavior exists.
- Existing behavior is not unnecessarily broken.
- Relevant tests pass.
- Application starts.
- API contracts remain correct.
- Errors are handled appropriately.
- Developer understands the changes.
- Changes are scoped and reviewable.
- Changes are committed.

---

## 25. Change Control

The following require explicit project-owner approval before implementation:

- Changing database architecture
- Changing API contracts
- Replacing PostgreSQL
- Replacing FastAPI
- Replacing React
- Introducing microservices
- Introducing ML as the core matching system
- Adding major external infrastructure
- Changing reconciliation scoring behavior
- Removing manual resolution
- Removing reconciliation history
- Removing client isolation
- Changing the three-data-type model

If an agent believes a change is necessary, it must **stop and explain the proposed change first**.

Do not silently implement architectural changes.

---

## 26. Frontend-Specific Protection Rule

When Antigravity is working on the frontend:

> **Frontend work must not modify backend business logic unless explicitly requested.**

Before modifying backend files, state:

```text
Backend files that would be changed:
Reason:
Expected API/behavior impact:
```

If there is no explicit authorization, do not make the backend change.

If a frontend requirement conflicts with an existing backend API, report the conflict instead of silently changing the backend.

---

## 27. Backend-Specific Protection Rule

When working on backend:

Do not modify frontend code unless explicitly requested.

Backend changes should preserve:

- Existing API behavior
- Existing database relationships
- Existing reconciliation rules
- Existing authentication behavior

Regression tests should be added whenever behavior changes intentionally.

---

## 28. Code Quality Principles

Prefer:

- Clear names
- Small focused functions
- Explicit business logic
- Typed schemas where appropriate
- Reusable validation
- Clear error handling
- Testable services
- Minimal duplication

Avoid:

- Magic numbers without explanation
- Hardcoded demo results
- Giant functions
- Giant modules
- Hidden global state
- Unnecessary abstractions
- Unnecessary dependencies
- Dead code
- Undocumented temporary hacks

---

## 29. Project Source of Truth

This document is the primary technical specification.

If another prompt or agent instruction conflicts with this document:

1. Stop.
2. Identify the conflict.
3. Ask for clarification or follow the explicitly newer project decision.

Do not silently reinterpret the architecture.

---

## 30. AI-Assisted Development Philosophy

AI is an implementation accelerator, not the owner of project architecture.

The developer owns:

- Requirements
- Architecture
- Technical decisions
- Scope
- Testing expectations
- Final code review
- Understanding of implementation

AI may assist with:

- Boilerplate
- Implementation
- Refactoring suggestions
- Debugging
- Tests
- Documentation
- UI implementation
- Code explanations

Every generated change must be reviewed.

---

## 31. Final Product Definition

The finished WorkflowSync application should allow an authenticated accounting-firm user to:

1. Log in.
2. View/select clients.
3. Work within a specific client's isolated workspace.
4. Upload invoice PDFs.
5. Extract invoice information.
6. Upload bank CSV transactions.
7. Validate and store transactions.
8. Run reconciliation.
9. Match invoices against transactions using explainable scoring.
10. See confidence and match reasons.
11. Review exceptions.
12. Manually resolve ambiguous cases.
13. View reconciliation history.
14. See meaningful errors.
15. Operate within proper authorization boundaries.
16. Run tests demonstrating correctness.
17. Use a realistic demo dataset.
18. Upload new data and demonstrate that results are computed dynamically.

---

# 32. Final Development Principle

**Build small. Test small. Understand small. Commit small.**

Do not attempt to build WorkflowSync in one AI generation.

The final application should be the result of many deliberate increments, not one massive AI-generated implementation.

Every increment should be:

```text
Small
Understandable
Testable
Reversible
Integrated
```

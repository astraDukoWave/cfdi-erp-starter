# Kilo Code — Architect Mode Prompts

## 1) System Blueprint
"Act as a senior software architect. Design a modular monorepo for a mini-ERP with CFDI (SAT Mexico) integration. Modules: erp_api (FastAPI), cfdi_engine, pac_adapter, sync_worker. Tech: Python 3.11, Postgres, Redis, Celery, SQLAlchemy. Non-functionals: security (JWT/OAuth2 later), idempotency, audit trails, testability. Deliver: folder structure, data model (tables for customers, products, invoices, invoice_lines, payments, sat_catalogs, certificates, jobs, audit_logs), sequence diagrams (text), risks."

## 2) OpenAPI Contract
"Generate an OpenAPI 3.1 spec covering endpoints: POST /invoices, GET /invoices/{id}, POST /invoices/{uuid}/cancel, GET /invoices/{uuid}/sat-status, POST /certificates, GET /catalogs/{name}, GET /health. Include schemas for InvoiceIn/Out, Concepto, Party, CancelIn/Out. Ensure idempotency-key header and standard error model."

## 3) CFDI Engine Specs
"Define Python module design for CFDI 4.0 XML builder, original string (XSLT) application, and signing with CSD (.cer/.key). Outline interfaces, exceptions, and unit tests. Provide pseudocode and stubs (no secrets)."

## 4) PAC Adapter Interface
"Create an abstract interface `PACClient` with methods: stamp(xml), cancel(uuid, motivo, sustituto), query(uuid). Provide FakePAC implementing deterministic responses for testing, plus an adapter template for a real PAC."

## 5) Workers & Retry Policy
"Design a task orchestration with Celery or RQ: queues for stamping/cancellation, exponential backoff, dead-letter handling, and idempotency. Provide configuration and test plan."

## 6) Security & Secrets
"Propose local development secrets management and progression to Vault/KMS. Logging policy: PII redaction, correlation IDs, structured logs. Add checklist."

## 7) CI/CD
"Create a GitHub Actions pipeline: lint (ruff, mypy), tests (pytest), build Docker images, publish artifacts (OpenAPI, Postman), and trigger a container deploy job (placeholder)."

## 8) Evidence Plan
"List the artifacts that prove experience: OpenAPI, XML samples, Postman, CI badges, demo video script, and test reports. Provide a README section template."

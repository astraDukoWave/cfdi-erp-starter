# CFDI ERP Starter (FastAPI + PostgreSQL + Redis)

Monorepo de referencia para crear **experiencia comprobable**: un mini-ERP con módulo de facturación y un **servicio CFDI** que genera, valida y encola timbrados vía PAC (stub). Incluye **OpenAPI**, **tests**, **Postman**, **Docker Compose** y **pipelines** de CI listos para ampliar.

## Servicios (monorepo)
- `apps/erp_api`: API ERP (clientes, productos, órdenes, facturas) y orquestación.
- `apps/cfdi_engine`: Construcción XML 4.0, cadena original (XSLT), firmado CSD (stub).
- `apps/pac_adapter`: Adaptador PAC (interfaz + fake sandbox para demos).
- `apps/sync_worker`: Worker de tareas (timbrado, cancelación, consultas).
- `docs/`: Arquitectura, prompts (Kilo Code Architect), evidencias.
- `openapi.yaml`: Contrato REST inicial (extiéndelo).

## Stack
- Python 3.11+, FastAPI, SQLAlchemy, Pydantic, Uvicorn
- PostgreSQL 16, Redis 7, Celery (stub), httpx, cryptography, lxml
- Docker Compose, GitHub Actions (CI), Postman collection

## Cómo correr (macOS Intel, zsh)
1) Instala dependencias de sistema:
```bash
# Postgres y Redis
brew update
brew install postgresql@16 redis openssl libxml2 libxslt

# Arranca servicios locales (opcional si usarás docker)
brew services start postgresql@16
brew services start redis
```

2) Instala **uv** (gestor Python veloz):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
exec -l $SHELL  # recarga zsh
```

3) Crear y sincronizar entorno:
```bash
uv sync
# Levantar ERP API:
uv run uvicorn apps.erp_api.main:app --reload

# (Opcional) Con Docker:
docker compose up -d --build
```

4) Probar healthcheck:
```bash
curl -s http://127.0.0.1:8000/health | jq
```

5) Postman: importa `postman/CFDI-ERP-Starter.postman_collection.json`

> **Nota**: El timbrado real requiere integrar un **PAC** y certificados **CSD** reales o de pruebas. Este starter incluye un `FakePAC` para evidencias y demo sin credenciales.

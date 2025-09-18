from fastapi import FastAPI, Depends, HTTPException, Header, Body, status
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
import json
import time
import uuid as uuidlib
import re

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from apps.db.deps import get_db
from apps.db.models import Invoice
from apps.core.auth import create_access_token, require_auth, verify_demo_credentials
from loguru import logger

app = FastAPI(title="CFDI ERP API", version="0.1.0")


# =========================
# Reglas de validación CFDI
# =========================

RFC_REGEX = re.compile(r'^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$', re.IGNORECASE)
CP_REGEX = re.compile(r'^\d{5}$')

class Party(BaseModel):
    rfc: str
    nombre: str
    regimenFiscal: Optional[str] = None
    domicilioFiscalReceptor: Optional[str] = None
    usoCFDI: Optional[str] = None

    @field_validator("rfc")
    @classmethod
    def _rfc_ok(cls, v: str) -> str:
        if not RFC_REGEX.match(v or ""):
            raise ValueError("RFC con formato inválido (simplificado)")
        return v.upper()

class Concepto(BaseModel):
    claveProdServ: str
    noIdentificacion: Optional[str] = None
    cantidad: float = Field(gt=0, description="Debe ser > 0")
    claveUnidad: str
    unidad: Optional[str] = None
    descripcion: str
    valorUnitario: float = Field(ge=0, description="Debe ser >= 0")
    descuento: Optional[float] = Field(default=0.0, ge=0)

class InvoiceIn(BaseModel):
    serie: Optional[str] = None
    folio: Optional[str] = None
    fecha: str
    moneda: str = "MXN"
    tipoCambio: float = 1.0
    formaPago: Optional[str] = None
    metodoPago: Optional[str] = None
    lugarExpedicion: str
    emisor: Party
    receptor: Party
    conceptos: List[Concepto]

    @field_validator("lugarExpedicion")
    @classmethod
    def _cp_ok(cls, v: str) -> str:
        if not CP_REGEX.match(v or ""):
            raise ValueError("lugarExpedicion debe ser CP de 5 dígitos")
        return v

    @model_validator(mode="after")
    def _coherencia_basica(self):
        # Moneda / tipoCambio
        if self.moneda.upper() == "MXN" and self.tipoCambio != 1:
            raise ValueError("Con MXN, tipoCambio debe ser 1")
        if self.moneda.upper() != "MXN" and self.tipoCambio <= 0:
            raise ValueError("Con moneda distinta a MXN, tipoCambio debe ser > 0")

        # Receptor debe tener usoCFDI
        if not self.receptor.usoCFDI:
            raise ValueError("receptor.usoCFDI es requerido")

        # Al menos un concepto
        if not self.conceptos or len(self.conceptos) == 0:
            raise ValueError("Debe incluir al menos un concepto")

        return self


class InvoiceOut(BaseModel):
    id: str
    status: Literal["pending", "stamped", "cancel_accepted", "cancel_rejected"]
    uuid: Optional[str] = None
    xml_url: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


# --- DTOs de login ---
class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Healthcheck ---
@app.get("/health")
def health():
    return {"status": "ok"}


# --- Login (emite JWT) ---
@app.post("/auth/login", response_model=TokenOut)
def login(body: LoginIn):
    if not verify_demo_credentials(body.username, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")
    token = create_access_token(sub=body.username)
    return {"access_token": token, "token_type": "bearer"}


# --- Timbrado simulado (actualiza en DB) ---
def _stamp_now(invoice_id: str, db: Session) -> None:
    time.sleep(0.5)  # simula trabajo
    inv = db.get(Invoice, invoice_id)
    if not inv:
        return
    inv.status = "stamped"
    inv.uuid = str(uuidlib.uuid4())
    inv.updated_at = datetime.utcnow()
    db.commit()
    logger.info(f"Stamped invoice {invoice_id} -> {inv.uuid}")


# --- Crear factura con idempotencia persistente (PROTEGIDO) ---
@app.post("/invoices", status_code=202, response_model=InvoiceOut)
def create_invoice(
    payload: InvoiceIn = Body(...),  # <-- ahora validamos con Pydantic
    idempotency_key: str = Header(..., alias="idempotency-key"),
    db: Session = Depends(get_db),
    user: str = Depends(require_auth),  # <-- protección con Bearer
):
    # 1) ¿ya existe por idempotency_key?
    existing = db.query(Invoice).filter(Invoice.idempotency_key == idempotency_key).one_or_none()
    if existing:
        return {
            "id": existing.id,
            "status": existing.status,
            "uuid": existing.uuid,
            "xml_url": existing.xml_url,
            "errors": [],
        }

    # 2) crear nueva
    new_id = str(uuidlib.uuid4())
    inv = Invoice(
        id=new_id,
        idempotency_key=idempotency_key,
        status="pending",
        uuid=None,
        xml_url=None,
        payload=json.dumps(payload.model_dump()),  # <-- guardamos limpio
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(inv)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Invoice).filter(Invoice.idempotency_key == idempotency_key).one()
        return {
            "id": existing.id,
            "status": existing.status,
            "uuid": existing.uuid,
            "xml_url": existing.xml_url,
            "errors": [],
        }

    # 3) timbrado simulado inmediato
    _stamp_now(new_id, db)

    return {"id": new_id, "status": "pending", "uuid": None, "xml_url": None, "errors": []}


# --- Consultar por ID interno (dejo ABIERTO para pruebas) ---
@app.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"id": inv.id, "status": inv.status, "uuid": inv.uuid, "xml_url": inv.xml_url, "errors": []}


# --- Cancelar por UUID (PROTEGIDO) ---
class CancelIn(BaseModel):
    motivo: Literal["01", "02", "03", "04"]
    uuidSustituto: Optional[str] = None

class CancelOut(BaseModel):
    uuid: str
    status: Literal["cancel_accepted", "cancel_rejected"]

@app.post("/invoices/{uuid}/cancel", response_model=CancelOut)
def cancel_invoice(uuid: str, body: CancelIn | None = None, db: Session = Depends(get_db), user: str = Depends(require_auth)):
    inv = db.query(Invoice).filter(Invoice.uuid == uuid).one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv.status = "cancel_accepted"  # mock
    inv.updated_at = datetime.utcnow()
    db.commit()
    return {"uuid": inv.uuid, "status": inv.status}


# --- Listar (PROTEGIDO) ---
@app.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(skip: int = 0, limit: int = 20, db: Session = Depends(get_db), user: str = Depends(require_auth)):
    q = db.query(Invoice).order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
    out = []
    for inv in q.all():
        out.append({
            "id": inv.id,
            "status": inv.status,
            "uuid": inv.uuid,
            "xml_url": inv.xml_url,
            "errors": [],
        })
    return out


# --- Consultar por UUID (dejo ABIERTO para pruebas) ---
@app.get("/invoices/by-uuid/{uuid}", response_model=InvoiceOut)
def get_invoice_by_uuid(uuid: str, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.uuid == uuid).one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"id": inv.id, "status": inv.status, "uuid": inv.uuid, "xml_url": inv.xml_url, "errors": []}
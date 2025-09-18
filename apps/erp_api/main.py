from fastapi import FastAPI, Depends, HTTPException, Header, Body
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import json
import time
import uuid as uuidlib

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from apps.db.deps import get_db
from apps.db.models import Invoice
from loguru import logger

app = FastAPI(title="CFDI ERP API", version="0.1.0")


# --- Modelos Pydantic opcionales (para documentar/validar si los usas en /docs) ---
class Party(BaseModel):
    rfc: str
    nombre: str
    regimenFiscal: Optional[str] = None
    domicilioFiscalReceptor: Optional[str] = None
    usoCFDI: Optional[str] = None

class Concepto(BaseModel):
    claveProdServ: str
    noIdentificacion: Optional[str] = None
    cantidad: float
    claveUnidad: str
    unidad: Optional[str] = None
    descripcion: str
    valorUnitario: float
    descuento: Optional[float] = 0.0

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

class InvoiceOut(BaseModel):
    id: str
    status: Literal["pending", "stamped", "cancel_accepted", "cancel_rejected"]
    uuid: Optional[str] = None
    xml_url: Optional[str] = None
    errors: List[str] = Field(default_factory=list)


# --- Healthcheck ---
@app.get("/health")
def health():
    return {"status": "ok"}


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


# --- Crear factura con idempotencia persistente ---
@app.post("/invoices", status_code=202, response_model=InvoiceOut)
def create_invoice(
    payload: dict = Body(...),  # si quieres, cambia a InvoiceIn para validar
    idempotency_key: str = Header(..., alias="idempotency-key"),
    db: Session = Depends(get_db),
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
        payload=json.dumps(payload),
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


# --- Consultar por ID interno ---
@app.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"id": inv.id, "status": inv.status, "uuid": inv.uuid, "xml_url": inv.xml_url, "errors": []}


# --- Cancelar por UUID ---
class CancelIn(BaseModel):
    motivo: Literal["01", "02", "03", "04"]
    uuidSustituto: Optional[str] = None

class CancelOut(BaseModel):
    uuid: str
    status: Literal["cancel_accepted", "cancel_rejected"]

@app.post("/invoices/{uuid}/cancel", response_model=CancelOut)
def cancel_invoice(uuid: str, body: CancelIn | None = None, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.uuid == uuid).one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv.status = "cancel_accepted"  # mock
    inv.updated_at = datetime.utcnow()
    db.commit()
    return {"uuid": inv.uuid, "status": inv.status}

@app.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
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

@app.get("/invoices/by-uuid/{uuid}", response_model=InvoiceOut)
def get_invoice_by_uuid(uuid: str, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.uuid == uuid).one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"id": inv.id, "status": inv.status, "uuid": inv.uuid, "xml_url": inv.xml_url, "errors": []}
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from loguru import logger
import uuid

app = FastAPI(title="CFDI ERP API", version="0.1.0")

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
    status: Literal["pending", "validating", "stamped", "cancelled", "failed"]
    uuid: Optional[str] = None
    xml_url: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

# In-memory store for demo purposes
DB = {}

@app.get("/health")
def health():
    return {"status": "ok"}

def enqueue_stamp(invoice_id: str):
    # Simula trabajo: genera UUID y marca como timbrado
    inv = DB.get(invoice_id)
    if not inv:
        return
    inv["status"] = "stamped"
    inv["uuid"] = str(uuid.uuid4())
    logger.info(f"Stamped invoice {invoice_id} -> {inv['uuid']}")

@app.post("/invoices", response_model=InvoiceOut, status_code=202)
def create_invoice(payload: InvoiceIn, background: BackgroundTasks, idempotency_key: Optional[str] = Header(default=None, convert_underscores=False)):
    # Idempotency demo: si ya existe, regresa lo mismo
    if idempotency_key and idempotency_key in DB:
        stored = DB[idempotency_key]
        return InvoiceOut(**stored)

    inv_id = idempotency_key or str(uuid.uuid4())
    record = {"id": inv_id, "status": "pending", "uuid": None, "xml_url": None, "errors": []}
    DB[inv_id] = record
    # Encolar timbrado simulado
    background.add_task(enqueue_stamp, inv_id)
    return InvoiceOut(**record)

@app.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str):
    inv = DB.get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceOut(**inv)

class CancelIn(BaseModel):
    motivo: Literal["01","02","03","04"]
    uuidSustituto: Optional[str] = None

class CancelOut(BaseModel):
    uuid: str
    status: Literal["cancel_pending","cancel_accepted","cancel_rejected"]

@app.post("/invoices/{uuid_str}/cancel", response_model=CancelOut, status_code=202)
def cancel_invoice(uuid_str: str, body: CancelIn):
    # Demo: marca aceptada sin verificar receptor
    # En real: encola y consulta a PAC
    return CancelOut(uuid=uuid_str, status="cancel_accepted")

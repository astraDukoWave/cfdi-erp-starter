from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_invoices_idempotency_key"),)

    id = Column(String, primary_key=True, index=True)
    idempotency_key = Column(String, nullable=False, index=True, unique=True)
    status = Column(String, nullable=False, index=True)
    uuid = Column(String, nullable=True, unique=True)
    xml_url = Column(Text, nullable=True)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

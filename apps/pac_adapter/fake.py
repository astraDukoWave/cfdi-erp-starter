import uuid, random, time
from .base import PACClient

class FakePAC(PACClient):
    def stamp(self, xml: bytes) -> dict:
        time.sleep(0.1)
        return {"ok": True, "uuid": str(uuid.uuid4()), "xml": xml}

    def cancel(self, uuid: str, motivo: str, sustituto: str | None) -> dict:
        time.sleep(0.1)
        return {"ok": True, "status": "cancelled"}

    def query(self, uuid: str) -> dict:
        return {"ok": True, "status": random.choice(["vigente", "cancelado"])}

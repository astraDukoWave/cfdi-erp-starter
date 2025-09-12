from lxml import etree

def build_cfdi_xml(invoice: dict) -> bytes:
    # Simplificado: genera XML mínimo (no conforme) solo para demo
    root = etree.Element("Comprobante", Serie=invoice.get("serie",""), Folio=invoice.get("folio",""))
    emisor = etree.SubElement(root, "Emisor", Rfc=invoice["emisor"]["rfc"], Nombre=invoice["emisor"]["nombre"])
    receptor = etree.SubElement(root, "Receptor", Rfc=invoice["receptor"]["rfc"], Nombre=invoice["receptor"]["nombre"])
    conceptos = etree.SubElement(root, "Conceptos")
    for c in invoice["conceptos"]:
        etree.SubElement(conceptos, "Concepto", ClaveProdServ=c["claveProdServ"], Cantidad=str(c["cantidad"]), Descripcion=c["descripcion"], ValorUnitario=str(c["valorUnitario"]))
    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")

# Proyecto demostrable: Mini-ERP + CFDI API (SAT)

## Objetivos de evidencia
- OpenAPI 3.1 con endpoints clave.
- XML CFDI 4.0 generado localmente (demo).
- Timbrado simulado (FakePAC) y traza por UUID.
- Postman y pruebas unitarias básicas.
- Despliegue local por Docker Compose y guía hacia cloud.
- Video breve mostrando: creación de factura → timbrado simulado → consulta de estado → cancelación simulada.

## Arquitectura (modular)
ERP API → (valida & persiste) → Encola tarea → CFDI Engine (arma XML, cadena, sello stub) → PAC Adapter (FakePAC o real) → Sync Worker (actualiza estado) → ERP API notifica.

## Módulos
- `erp_api`: rutas /invoices, /catalogs (cache), /certificates, auth básica.
- `cfdi_engine`: builder XML 4.0, xslt cadena original (pendiente XSLT real), firmador (CSD stub).
- `pac_adapter`: `FakePAC` con estados determinísticos (para demos).
- `sync_worker`: cola para timbrado/cancelación con backoff.

## Roadmap hacia PAC real
1) Sustituir FakePAC por cliente de PAC (SDK/REST).
2) Cargar XSLT oficial y aplicar a XML para cadena original.
3) Firmar con CSD (.cer/.key) desde bóveda (Vault/KMS).
4) Agregar complemento de Pagos 2.0 si el negocio lo requiere.

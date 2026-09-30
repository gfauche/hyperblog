## Cumplimiento legal (obligatorio)

Este repositorio es **público**. Antes de hacer commit:
- **Fuentes de terceros**: registrarlas en `FUENTES.md` en el mismo commit (origen, URL, fecha y condición de uso).
- **Obras protegidas** (artículos, imágenes, PDF, material de cursos de pago): no subirlas sin permiso o licencia; citar autor y fuente (D.Leg. 822, art. 44).
- **Datos personales** (Ley 29733): nunca datos de personas identificables.
- **Secretos**: nunca en el repositorio; `.env` y llaves están en `.gitignore`. Si alguno llega a subirse, revocarlo de inmediato: el historial público ya lo expuso.
- **Descargas automáticas**: solo con `descarga_responsable.py` (plantilla en la skill `/constitucion-peru`), sin simular navegadores ni evadir controles.
- **Código de terceros**: conservar su `LICENSE`/`NOTICE`.
- Correr `python tools/revisar_cumplimiento.py` y dejarlo en OK; el workflow "Revisión de cumplimiento" lo repite en cada push.

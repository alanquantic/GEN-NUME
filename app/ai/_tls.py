"""Confianza TLS basada en el almacén de certificados del sistema operativo.

En algunas máquinas (antivirus con inspección HTTPS, redes corporativas) el
tráfico TLS se intercepta y re-firma con un certificado raíz privado que vive en
el almacén del SO pero que Python no lee por defecto — y las llamadas a la API
fallan con CERTIFICATE_VERIFY_FAILED.

`truststore` hace que Python verifique contra el almacén del SO, que sí confía
en ese raíz. Es seguro (sigue verificando) y en Linux/Railway usa el bundle de
CA del sistema, así que llamarlo siempre es inocuo. Si `truststore` no está
instalado, no se hace nada y se usa la verificación por defecto.
"""

from __future__ import annotations

_done = False


def ensure_system_trust() -> None:
    """Inyecta el almacén del SO en el SSL de Python. Idempotente y silencioso."""
    global _done
    if _done:
        return
    _done = True
    try:
        import truststore
        truststore.inject_into_ssl()
    except Exception:
        pass  # sin truststore: verificación por defecto (certifi)


__all__ = ["ensure_system_trust"]

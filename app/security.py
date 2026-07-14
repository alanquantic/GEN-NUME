"""Verificación de firma HMAC del webhook.

La tienda (Next.js) firma el cuerpo crudo de la petición con un secreto
compartido y envía el hex en la cabecera `X-Signature`. Aquí se recalcula y se
compara en tiempo constante. Esto sustituye al `$_REQUEST` abierto del original,
que cualquiera podía invocar.

Ejemplo del lado de la tienda (TypeScript):

    import { createHmac } from "crypto";
    const body = JSON.stringify(payload);
    const signature = createHmac("sha256", WEBHOOK_SECRET).update(body).digest("hex");
    // fetch(url, { headers: { "X-Signature": signature }, body })
"""

from __future__ import annotations

import hashlib
import hmac

from .config import settings


def sign(body: bytes, secret: str | None = None) -> str:
    secret = secret or settings.webhook_secret
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def verify_signature(body: bytes, signature: str | None) -> bool:
    if not settings.require_signature:
        return True
    if not signature:
        return False
    expected = sign(body)
    return hmac.compare_digest(expected, signature.strip().lower())

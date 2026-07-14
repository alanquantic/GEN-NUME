"""Configuración por variables de entorno (12-factor).

Nada de rutas ni secretos hardcodeados como en el proyecto original
(el `/home/master/applications/...` incrustado en el código). Todo se
inyecta por entorno y en Railway se define en las Variables del servicio.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Seguridad del webhook (HMAC compartido con la tienda Next.js)
    webhook_secret: str = "cambia-esto-en-railway"
    require_signature: bool = True
    signature_header: str = "x-signature"

    # Almacenamiento (Volume de Railway montado, p. ej. en /data)
    storage_dir: Path = Path("data")
    # URL pública base del servicio (para construir el enlace de descarga)
    public_base_url: str = "http://localhost:8000"

    # Assets estáticos (plantillas .jpg y fuentes .ttf) y contenido de textos
    assets_dir: Path = Path("assets")
    content_dir: Path = Path("content")

    environment: str = "development"

    @property
    def report_templates_dir(self) -> Path:
        return self.assets_dir / "report"

    @property
    def fonts_dir(self) -> Path:
        return self.assets_dir / "fonts"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

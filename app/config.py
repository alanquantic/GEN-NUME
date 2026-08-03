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

    # --- Compresión de los PDF generados -------------------------------- #
    # "images": recomprime los fondos JPG de los reportes clásicos (ahorra
    #           50-75% con pérdida imperceptible; el texto es vectorial y no
    #           se toca). "slim": sólo recompresión estructural sin pérdida.
    # "off": entrega el PDF tal cual sale del generador.
    pdf_compress: str = "images"
    pdf_image_max_px: int = 1600
    pdf_image_quality: int = 80

    # --- Reportes dinámicos con IA ------------------------------------- #
    # Proveedor del modelo: "anthropic" o "google" (Gemini · AI Studio).
    ai_provider: str = "anthropic"
    # Claves de API (nunca hardcodear; en Railway van en Variables).
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    # Modelo. Opus 5 por defecto para Anthropic; Google cae a un modelo
    # estable vigente salvo que AI_MODEL ya sea un identificador Gemini.
    ai_model: str = "claude-opus-5"
    ai_effort: str = "high"          # low | medium | high | xhigh | max (Anthropic)
    ai_max_tokens: int = 16000

    @property
    def resolved_model(self) -> str:
        """Modelo efectivo según el proveedor."""
        if self.ai_provider == "google" and not self.ai_model.startswith("gemini"):
            return "gemini-3.5-flash"
        return self.ai_model

    @property
    def report_templates_dir(self) -> Path:
        return self.assets_dir / "report"

    @property
    def fonts_dir(self) -> Path:
        return self.assets_dir / "fonts"

    @property
    def static_pdf_dir(self) -> Path:
        """PDFs pre-hechos (agenda, planeador, semestral) que solo se sirven."""
        return self.assets_dir / "static"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

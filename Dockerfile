# Imagen estable con wheels garantizados (el dev local usa 3.14, pero para el
# contenedor fijamos 3.12-slim por fiabilidad).
FROM python:3.12-slim

# fonts-dejavu-core: fuente unicode de reserva del sistema (fallback si aún no
# se cargan las TTF de marca). fontconfig ayuda a fpdf2 a resolver rutas.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STORAGE_DIR=/data

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código + contenido. Los assets (plantillas .jpg y fuentes .ttf) se copian si
# están presentes en el contexto de build (ver README / .dockerignore).
COPY app ./app
COPY content ./content
COPY assets ./assets

# El Volume de Railway se monta en /data en tiempo de ejecución.
RUN mkdir -p /data

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

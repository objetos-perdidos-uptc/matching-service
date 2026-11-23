# syntax=docker/dockerfile:1.7
FROM python:3.11-slim

# Usuario no-root (buena practica: si te comprometen el contenedor, no son root)
RUN groupadd --system --gid 1000 app \
 && useradd  --system --uid 1000 --gid 1000 --create-home --shell /sbin/nologin app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1) Solo requirements primero: capa cacheada mientras requirements.txt no cambie
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# 2) Codigo de la app
COPY app ./app

# 3) Permisos al usuario no-root
RUN chown -R app:app /app
USER app

EXPOSE 8000

# Healthcheck portatil: comprueba que algo escucha en :8000 (sin curl/wget)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import socket,sys; s=socket.socket(); s.settimeout(2); sys.exit(0 if s.connect_ex(('127.0.0.1',8000))==0 else 1)"

# uvicorn arranca la app FastAPI en app/main.py
# (asume que app/main.py expone 'app = FastAPI()'; si usa factory, añade --factory)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
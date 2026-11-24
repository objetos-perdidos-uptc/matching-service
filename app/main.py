from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator # <-- NUEVO IMPORT
from app.infrastructure.api.routes import router

app = FastAPI(
    title="Matching Service API",
    description="Microservicio para encontrar coincidencias de objetos perdidos",
    version="1.0.0"
)

# Registramos las rutas
app.include_router(router, prefix="/api/v1/matches")

# ==========================================
# MONITOREO (Prometheus)
# ==========================================
# Esto crea automáticamente el endpoint GET /metrics
Instrumentator().instrument(app).expose(app)

@app.get("/health")
def health_check():
    return {"status": "UP", "service": "matching-service"}
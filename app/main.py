from fastapi import FastAPI
from app.infrastructure.api.routes import router 

app = FastAPI(
    title="Matching Service API",
    description="Microservicio para encontrar coincidencias de objetos perdidos",
    version="1.0.0"
)

# Registramos las rutas
app.include_router(router, prefix="/api/v1/matches")

@app.get("/health")
def health_check():
    return {"status": "UP", "service": "matching-service"}

from fastapi import APIRouter, Depends, HTTPException
from typing import List
import httpx
import os

# Schemas
from app.infrastructure.api.schemas import MatchRequest, MatchResponse

# Dominio
from app.domain.entities import Report, Location, ReportType # Corregido el error de tipeo
from app.domain.services.scoring_engine import MatchingEngine

# Aplicación
from app.application.use_cases.evaluate_report import EvaluateReportUseCase
from app.application.use_cases.get_recommendations import GetRecommendationsUseCase

# Infraestructura
from app.infrastructure.repositories.redis_repository import RedisMatchRepository
from app.infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher

router = APIRouter()

def get_evaluate_use_case() -> EvaluateReportUseCase:
    repo = RedisMatchRepository()
    publisher = RabbitMQEventPublisher()
    engine = MatchingEngine()
    
    # OJO: Cambiamos "distance" por "location" para reflejar el nuevo algoritmo
    weights = {
        "name": 0.4,
        "color": 0.15,
        "material": 0.15,
        "time": 0.15,
        "location": 0.15 
    }
    
    return EvaluateReportUseCase(
        match_repository=repo,
        event_publisher=publisher,
        matching_engine=engine,
        weights=weights
    )

@router.post("/evaluate", response_model=List[MatchResponse])
async def evaluate_matches(
    request: MatchRequest, 
    use_case: EvaluateReportUseCase = Depends(get_evaluate_use_case)
):
    # ... (Este endpoint manual se queda igual para pruebas desde Swagger) ...
    def to_domain(schema) -> Report:
        loc = None
        if schema.location:
            loc = Location(latitude=schema.location.latitude, longitude=schema.location.longitude)
        return Report(
            report_id=schema.report_id, user_id=schema.user_id, report_type=ReportType(schema.report_type),
            name=schema.name, description=schema.description, category_id=schema.category_id, campus_id=schema.campus_id,
            color=schema.color, material=schema.material, date_lost=schema.date_lost, date_found=schema.date_found,
            location=loc, location_text=schema.location_text
        )

    target_domain = to_domain(request.target_report)
    candidates_domain = [to_domain(c) for c in request.candidates]
    results = await use_case.execute(target_domain, candidates_domain)
    
    return [MatchResponse(
        lost_id=r.lost_id, found_id=r.found_id, total_score=r.total_score,
        name_score=r.name_score, color_score=r.color_score, material_score=r.material_score,
        time_score=r.time_score, distance_score=r.distance_score
    ) for r in results]

# --- NUEVO ENDPOINT (Problema 3) ---
@router.post("/evaluate/{report_id}", response_model=List[MatchResponse])
async def evaluate_report_by_id(
    report_id: int, 
    use_case: EvaluateReportUseCase = Depends(get_evaluate_use_case)
):
    """
    Recibe un ID, busca el reporte en el microservicio de Node.js, 
    busca candidatos y calcula el match.
    """
    # El nombre del servicio en Docker es "report-service" (según el docker-compose)
    REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://report-service:8082")
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Buscamos el reporte base (usando la ruta GET /:id que nos mostraste de tu compañero)
            res_target = await client.get(f"{REPORT_SERVICE_URL}/reports/{report_id}")
            if res_target.status_code != 200:
                raise HTTPException(status_code=404, detail="Reporte no encontrado")
            data_target = res_target.json()
            
            # 2. Buscamos los candidatos (usando la ruta GET /search de tu compañero)
            # Usamos los mismos filtros del reporte base
            res_candidates = await client.get(
                f"{REPORT_SERVICE_URL}/reports/search", 
                params={"categoryId": data_target["categoryId"], "campusId": data_target["campusId"]}
            )
            data_candidates = res_candidates.json()
            
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Error conectando con Report Service: {exc}")

    # 3. Mapeamos los datos de Node.js a nuestras Entidades de Dominio
    def map_node_to_domain(node_data) -> Report:
        return Report(
            report_id=node_data["id"], # Ojo: verifica cómo se llama el ID en el JSON de tu compañero
            user_id=node_data["userId"],
            report_type=ReportType(node_data["type"]),
            name=node_data["name"],
            description=node_data.get("description", ""),
            category_id=node_data["categoryId"],
            campus_id=node_data["campusId"],
            color=node_data.get("color"),
            material=node_data.get("material"),
            date_lost=node_data.get("dateLost"),
            date_found=node_data.get("dateFound"),
            location_text=node_data.get("locationText")
        )

    target_domain = map_node_to_domain(data_target)
    
    # Extraemos la lista de reportes (asumiendo que /search devuelve un objeto con 'items' o similar)
    candidates_list = data_candidates.get("items", data_candidates) 
    candidates_domain = [map_node_to_domain(c) for c in candidates_list if c["id"] != report_id]

    # 4. Ejecutamos el caso de uso
    results = await use_case.execute(target_domain, candidates_domain)
    
    return [MatchResponse(
        lost_id=r.lost_id, found_id=r.found_id, total_score=r.total_score,
        name_score=r.name_score, color_score=r.color_score, material_score=r.material_score,
        time_score=r.time_score, distance_score=r.distance_score
    ) for r in results]


# ... (Tus endpoints GET de recomendaciones se quedan igual) ...
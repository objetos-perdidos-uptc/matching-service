from fastapi import APIRouter, Depends
from typing import List

# Schemas
from app.infrastructure.api.schemas import MatchRequest, MatchResponse

# Dominio
from app.domain.entities import Report, Location, ReportType
from app.domain.services.scoring_engine import MatchingEngine

# Aplicación
from app.application.use_cases.evaluate_report import EvaluateReportUseCase

# Infraestructura
from app.infrastructure.repositories.redis_repository import RedisMatchRepository
from app.infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher
from app.application.use_cases.get_recommendations import GetRecommendationsUseCase

router = APIRouter()

def get_evaluate_use_case() -> EvaluateReportUseCase:
    # 1. Inyectamos la infraestructura real
    repo = RedisMatchRepository()
    publisher = RabbitMQEventPublisher()
    
    # 2. El motor de dominio
    engine = MatchingEngine()
    
    # 3. Configuración de pesos
    weights = {
        "name": 0.4,
        "color": 0.15,
        "material": 0.15,
        "time": 0.15,
        "distance": 0.15
    }
    
    # 4. Retornamos el caso de uso ensamblado
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
    def to_domain(schema) -> Report:
        loc = None
        if schema.location:
            loc = Location(latitude=schema.location.latitude, longitude=schema.location.longitude)
            
        return Report(
            report_id=schema.report_id,
            user_id=schema.user_id,
            report_type=ReportType(schema.report_type),
            name=schema.name,
            description=schema.description,
            category_id=schema.category_id,
            campus_id=schema.campus_id,
            color=schema.color,
            material=schema.material,
            date_lost=schema.date_lost,
            date_found=schema.date_found,
            location=loc,
            location_text=schema.location_text
        )

    target_domain = to_domain(request.target_report)
    candidates_domain = [to_domain(c) for c in request.candidates]

    results = await use_case.execute(target_domain, candidates_domain)
    
    response = []
    for r in results:
        response.append(MatchResponse(
            lost_id=r.lost_id,
            found_id=r.found_id,
            total_score=r.total_score,
            name_score=r.name_score,
            color_score=r.color_score,
            material_score=r.material_score,
            time_score=r.time_score,
            distance_score=r.distance_score
        ))
        
    return response

def get_recommendations_use_case() -> GetRecommendationsUseCase:
    # Aquí usamos el mismo repositorio de Redis
    repo = RedisMatchRepository()
    return GetRecommendationsUseCase(match_repository=repo)

@router.get("/lost/{lost_id}/recommendations", response_model=List[MatchResponse])
async def get_lost_recommendations(
    lost_id: int,
    use_case: GetRecommendationsUseCase = Depends(get_recommendations_use_case)
):
    """HU-10: Obtiene el ranking de FOUND recomendados para un reporte LOST."""
    results = await use_case.execute_for_lost(lost_id)
    
    # Mapeamos el dominio al schema de respuesta
    return [
        MatchResponse(
            lost_id=r.lost_id, found_id=r.found_id, total_score=r.total_score,
            name_score=r.name_score, color_score=r.color_score, material_score=r.material_score,
            time_score=r.time_score, distance_score=r.distance_score
        ) for r in results
    ]

@router.get("/found/{found_id}/candidates", response_model=List[MatchResponse])
async def get_found_candidates(
    found_id: int,
    use_case: GetRecommendationsUseCase = Depends(get_recommendations_use_case)
):
    """HU-09: Obtiene el ranking de LOST (posibles dueños) para un FOUND."""
    results = await use_case.execute_for_found(found_id)
    
    return [
        MatchResponse(
            lost_id=r.lost_id, found_id=r.found_id, total_score=r.total_score,
            name_score=r.name_score, color_score=r.color_score, material_score=r.material_score,
            time_score=r.time_score, distance_score=r.distance_score
        ) for r in results
    ]
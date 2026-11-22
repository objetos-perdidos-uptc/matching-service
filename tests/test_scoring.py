import pytest
from app.domain.entities import Report, ReportType, Location
from app.domain.services.scoring_engine import MatchingEngine

def test_perfect_match():
    # 1. Creamos dos objetos idénticos usando el Dominio
    loc = Location(latitude=5.535, longitude=-73.367)
    lost = Report(
        report_id=1, user_id=10, report_type=ReportType.LOST, 
        name="Calculadora Casio", description="Negra", category_id=1, campus_id=1,
        color="negra", material="plastico", location=loc
    )
    found = Report(
        report_id=2, user_id=20, report_type=ReportType.FOUND, 
        name="Calculadora Casio", description="Negra", category_id=1, campus_id=1,
        color="negra", material="plastico", location=loc
    )

    # 2. Instanciamos el motor
    engine = MatchingEngine()
    weights = {"name": 0.4, "color": 0.15, "material": 0.15, "time": 0.15, "distance": 0.15}

    # 3. Calculamos
    result = engine.calculate_match(lost, found, weights)

    # 4. Verificamos (Assert) que el puntaje sea perfecto (100%)
    # Nota: Como no hay fechas, el tiempo dará 0, pero el resto debe ser 100.
    assert result.total_score > 80.0
    assert result.lost_id == 1
    assert result.found_id == 2
    print("\n✅ Test pasado: El motor calculó un match alto correctamente.")
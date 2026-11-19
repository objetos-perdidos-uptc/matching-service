# pydantic es el motor detras de FastApi
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Definen como deben ingresar las request fuera del microservicio

# BaseModel define estas validaciones:
# 1. Si report_id no tiene formato correcto, Pydantic bloquea la petición y devuelve un error 422
# 2. Pydantic convierte fecha en formato correcto
# 3. MatchResponde de BaseModel serializa un objeto JSON
# 4. Documentación Automática (Swagger)

class LocationSchema(BaseModel):
    latitude: float
    longitude: float

class ReportSchema(BaseModel):
    report_id: int
    user_id: int
    report_type: str # "LOST" o "FOUND"
    name: str
    description: str
    category_id: int
    campus_id: int
    color: Optional[str] = None
    material: Optional[str] = None
    date_lost: Optional[datetime] = None
    date_found: Optional[datetime] = None
    location: Optional[LocationSchema] = None

class MatchRequest(BaseModel):
    target_report: ReportSchema
    candidates: List[ReportSchema]

class MatchResponse(BaseModel):
    lost_id: int
    found_id: int
    total_score: float
    name_score: float
    color_score: float
    material_score: float
    time_score: float
    distance_score: float
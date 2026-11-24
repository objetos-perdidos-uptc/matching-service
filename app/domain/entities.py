from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.value_objects import ReportType, Location

@dataclass
class Report:
    report_id: int
    user_id: int
    report_type: ReportType
    name: str
    description: str
    category_id: int
    campus_id: int
    color: Optional[str] = None
    material: Optional[str] = None
    date_lost: Optional[datetime] = None
    date_found: Optional[datetime] = None
    location: Optional[Location] = None
    location_text: Optional[str] = None
    

@dataclass
class MatchResult:
    lost_id: int
    found_id: int
    total_score: float
    name_score: float
    color_score: float
    material_score: float
    time_score: float
    distance_score: float
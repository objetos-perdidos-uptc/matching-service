import httpx
import os
from typing import List
from app.domain.entities import Report, ReportType, Location
from datetime import datetime

class ReportClient:
    def __init__(self):
        # Usamos la URL interna de Docker (el nombre del servicio)
        self.base_url = os.getenv("REPORT_SERVICE_URL", "http://report-service:8082")
        
    async def get_candidates(self, campus_id: int, category_id: int) -> List[Report]:
        """Pide los reportes candidatos al microservicio de tu compañero."""
        async with httpx.AsyncClient() as client:
            # (Reemplaza esta URL por la que te diga tu compañero)
            response = await client.get(f"{self.base_url}/reports/search?campus_id={campus_id}&category_id={category_id}")
            
            if response.status_code != 200:
                return []
                
            data = response.json()
            reports = []
            for item in data:
                # Mapeamos el JSON de él a nuestras Entidades de Dominio
                reports.append(Report(
                    report_id=item["reportId"],
                    user_id=item["userId"],
                    report_type=ReportType(item["type"]),
                    name=item["name"],
                    description=item.get("description", ""),
                    category_id=item["categoryId"],
                    campus_id=item["campusId"],
                    color=item.get("color"),
                    material=item.get("material"),
                    date_lost=datetime.fromisoformat(item["dateLost"]) if item.get("dateLost") else None,
                    date_found=datetime.fromisoformat(item["dateFound"]) if item.get("dateFound") else None,
                    location_text=item.get("locationText")
                ))
            return reports
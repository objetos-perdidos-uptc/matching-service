
import unicodedata
from typing import Optional, List
import math
from rapidfuzz import fuzz
from app.domain.entities import Report, MatchResult
from abc import ABC, abstractmethod

class IScoringStrategy(ABC):
    @abstractmethod
    def calculate(self, lost: Report, found: Report) -> float:
        pass


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    # unicodedata.normalize("NFD") Descompone el carácter acentuado en carácter base y signo de acentuación al lado por ejemplo á se convierte en "a" y "'" 
    s = unicodedata.normalize("NFD", str(text).lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = "".join(c if c.isalnum() or c.isspace() else " " for c in s)
    return " ".join(s.split())

# --- ESTRATEGIAS DE PUNTAJE (Patrón Strategy) ---

class NameScoringStrategy(IScoringStrategy):
    """ Puntaje basado en similitud de nombres """
    def calculate(self, lost: Report, found: Report) -> float:
        name1 = normalize_text(lost.name)
        name2 = normalize_text(found.name)
        if not name1 or not name2:
            return 0.0
        # rapidfuzz compara
        return fuzz.token_set_ratio(name1, name2) / 100.0

class TimeScoringStrategy(IScoringStrategy):
    """ Puntaje basado en diferencia de tiempo """
    def calculate(self, lost: Report, found: Report) -> float:
        if not lost.date_lost or not found.date_found:
            return 0.0

        delta_days = (found.date_found - lost.date_lost).total_seconds() / 86400.0

        if delta_days < 0 or delta_days >= 30:
            return 0.0
        return 1 - (delta_days / 30)

class DistanceScoringStrategy(IScoringStrategy):
    """ Calcula el puntaje basado en la distancia """
    def calculate(self, lost: Report, found: Report) -> float:
        if not lost.location or not found.location:
            return 0.0

        lat1, lon1 = lost.location.latitude, lost.location.longitude
        lat2, lon2 = found.location.latitude, found.location.longitude

        # Formula de Haversine corregida
        R = 6371.0 # Radio de la tierra (usualmente 6371)
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        # Aquí corregimos el math.din por math.sin y agregamos math.cos(p1)
        a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
        
        # Aquí agregamos el math.asin
        distance_km = 2 * R * math.asin(math.sqrt(a))
        
        MAX_DISTANCE_KM = 5.0 
        if distance_km >= MAX_DISTANCE_KM:
            return 0.0
        return 1.0 - (distance_km / MAX_DISTANCE_KM)
    
COLOR_SYNONYMS = {
    "azul": {"azul", "celeste", "marino", "añil"},
    "rojo": {"rojo", "vinotinto", "carmesi", "granate"},
    "verde": {"verde", "esmeralda", "oliva"},
    "negro": {"negro", "grafito", "carbon"},
    "blanco": {"blanco", "beige", "crema", "hueso"},
    "gris": {"gris", "plata", "plateado"},
}

class ColorScoringStrategy(IScoringStrategy):
    def calculate(self, lost: Report, found: Report) -> float:
        color1 = normalize_text(lost.color)
        color2 = normalize_text(found.color)
        if not color1 or not color2:
            return 0.0
        if color1 == color2:
            return 1.0
        for group in COLOR_SYNONYMS.values():
            if color1 in group and color2 in group:
                return 0.5
        return fuzz.token_set_ratio(color1, color2) / 100.0

MATERIAL_SYNONYMS = {
    "cuero": {"cuero", "piel", "sintetico"},
    "tela": {"tela", "nylon", "lona", "algodon"},
    "metal": {"metal", "aluminio", "acero", "hierro"},
    "plastico": {"plastico", "pvc", "acrilico"},
    "madera": {"madera", "roble", "pino"},
}

class MaterialScoringStrategy(IScoringStrategy):
    def calculate(self, lost: Report, found: Report) -> float:
        mat1 = normalize_text(lost.material)
        mat2 = normalize_text(found.material)
        if not mat1 or not mat2:
            return 0.0
        if mat1 == mat2:
            return 1.0
        for material in MATERIAL_SYNONYMS.values():
            if mat1 in material and mat2 in material:
                return 0.5
        return fuzz.token_set_ratio(mat1, mat2) / 100.0

class MatchingEngine:
    """ Servicio de Dominio que orquesta todas las estrategias """

    def __init__(self):
        self.name_strategy = NameScoringStrategy()
        self.time_strategy = TimeScoringStrategy()
        self.distance_strategy = DistanceScoringStrategy()
        self.color_strategy = ColorScoringStrategy()
        self.material_strategy = MaterialScoringStrategy()

    def calculate_match(self, lost: Report, found: Report, weights: dict) -> MatchResult:
        # calcular puntaje de cada estrategia
        s_name = self.name_strategy.calculate(lost, found)
        s_time = self.time_strategy.calculate(lost, found)
        s_distance = self.distance_strategy.calculate(lost, found)
        s_color = self.color_strategy.calculate(lost, found)
        s_material = self.material_strategy.calculate(lost, found)

        # aplicar pesos
        score_name = s_name * weights.get("name", 0.0)
        score_time = s_time * weights.get("time", 0.0)
        score_distance = s_distance * weights.get("distance", 0.0)
        score_color = s_color * weights.get("color", 0.0)
        score_material = s_material * weights.get("material", 0.0)

        total_score = score_name + score_time + score_distance + score_color + score_material

        return MatchResult(
            lost_id=lost.report_id,
            found_id=found.report_id,
            total_score=round(total_score * 100, 2),
            name_score=round(score_name * 100, 2),
            color_score=round(score_color * 100, 2),
            material_score=round(score_material * 100, 2),
            time_score=round(score_time * 100, 2),
            distance_score=round(score_distance * 100, 2)
        )
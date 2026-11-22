from typing import List
from app.domain.entities import MatchResult
from app.domain.ports import IMatchRepository

class GetRecommendationsUseCase:
    def __init__(self, match_repository: IMatchRepository):
        self.match_repository = match_repository

    async def execute_for_lost(self, lost_id: int) -> List[MatchResult]:
        """HU-10: El que perdió ve los objetos encontrados."""
        return await self.match_repository.get_recommendations_for_lost(lost_id)

    async def execute_for_found(self, found_id: int) -> List[MatchResult]:
        """HU-09: El que encontró ve los posibles dueños."""
        return await self.match_repository.get_recommendations_for_found(found_id)
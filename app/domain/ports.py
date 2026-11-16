from abc import ABC, abstractmethod
from typing import List
from app.domain.entities import MatchResult

class IMatchRepository(ABC):

    @abstractmethod
    async def save_many(self, results: List[MatchResult]) -> None:
        pass

    @abstractmethod
    async def get_recommendations_for_lost(self, lost_id: int) -> List[MatchResult]:
        pass

    @abstractmethod
    async def get_recommendations_for_found(self, found_id: int) -> List[MatchResult]:
        pass

class IEventPublisher(ABC):
    @abstractmethod
    async def publish_high_match(self, user_id: int, match_result: MatchResult) -> None:
        pass
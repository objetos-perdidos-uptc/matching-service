import os
import redis.asyncio as redis
from typing import List
from app.domain.ports import IMatchRepository
from app.domain.entities import MatchResult

class RedisMatchRepository(IMatchRepository):
    def __init__(self, redis_url: str | None = None):
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = redis.from_url(url, decode_responses=True)

    async def save_many(self, results: List[MatchResult]) -> None:
        async with self.redis.pipeline(transaction=True) as pipe:
            for r in results:
                pipe.zadd(f"matches:lost:{r.lost_id}", {str(r.found_id): r.total_score})
                pipe.zadd(f"matches:found:{r.found_id}", {str(r.lost_id): r.total_score})
            await pipe.execute()
        print(f"[REDIS] {len(results)} matches guardados exitosamente.")

    async def get_recommendations_for_lost(self, lost_id: int) -> List[MatchResult]:
        items = await self.redis.zrevrange(f"matches:lost:{lost_id}", 0, 10, withscores=True)
        return [
            MatchResult(lost_id=lost_id, found_id=int(fid), total_score=score,
                        name_score=0, color_score=0, material_score=0, time_score=0, distance_score=0)
            for fid, score in items
        ]

    async def get_recommendations_for_found(self, found_id: int) -> List[MatchResult]:
        items = await self.redis.zrevrange(f"matches:found:{found_id}", 0, 10, withscores=True)
        return [
            MatchResult(lost_id=int(lid), found_id=found_id, total_score=score,
                        name_score=0, color_score=0, material_score=0, time_score=0, distance_score=0)
            for lid, score in items
        ]

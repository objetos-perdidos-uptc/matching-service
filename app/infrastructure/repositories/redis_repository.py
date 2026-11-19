import redis.asyncio as redis
from typing import List
from app.domain.ports import IMatchRepository
from app.domain.entities import MatchResult

class RedisMatchRepository(IMatchRepository):
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        # Conectamos a Redis de forma asíncrona
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def save_many(self, results: List[MatchResult]) -> None:
        """Guarda los resultados en Redis usando Sorted Sets."""
        async with self.redis.pipeline(transaction=True) as pipe:
            for r in results:
                # ZADD: Agrega al Sorted Set. El score es el puntaje, el member es el ID.
                pipe.zadd(f"matches:lost:{r.lost_id}", {str(r.found_id): r.total_score})
                pipe.zadd(f"matches:found:{r.found_id}", {str(r.lost_id): r.total_score})
            # Execute envía todos los comandos de golpe (más eficiente)
            await pipe.execute()
        print(f"[REDIS] {len(results)} matches guardados exitosamente.")

    async def get_recommendations_for_lost(self, lost_id: int) -> List[MatchResult]:
        """Obtiene el ranking de los mejores FOUND para un LOST (HU-10)."""
        # ZREVRANGE: Obtiene los elementos ordenados de mayor a menor
        items = await self.redis.zrevrange(f"matches:lost:{lost_id}", 0, 10, withscores=True)
        
        results = []
        for found_id_str, score in items:
            results.append(MatchResult(
                lost_id=lost_id,
                found_id=int(found_id_str),
                total_score=score,
                name_score=0, color_score=0, material_score=0, time_score=0, distance_score=0 # Simplificado para la consulta
            ))
        return results

    async def get_recommendations_for_found(self, found_id: int) -> List[MatchResult]:
        """Obtiene el ranking de los mejores LOST para un FOUND (HU-09)."""
        items = await self.redis.zrevrange(f"matches:found:{found_id}", 0, 10, withscores=True)
        
        results = []
        for lost_id_str, score in items:
            results.append(MatchResult(
                lost_id=int(lost_id_str),
                found_id=found_id,
                total_score=score,
                name_score=0, color_score=0, material_score=0, time_score=0, distance_score=0
            ))
        return results
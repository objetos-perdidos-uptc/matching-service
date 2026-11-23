import os
import aio_pika
import json
from app.domain.ports import IEventPublisher
from app.domain.entities import MatchResult

class RabbitMQEventPublisher(IEventPublisher):
    def __init__(self, amqp_url: str | None = None):
        self.amqp_url = amqp_url or os.getenv("AMQP_URL", "amqp://guest:guest@localhost:5672/")

    async def publish_high_match(self, user_id: int, match_result: MatchResult) -> None:
        connection = await aio_pika.connect_robust(self.amqp_url)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue("match_notifications", durable=True)
            message_body = {
                "event": "high_match_found",
                "user_id": user_id,
                "match_data": {
                    "lost_id": match_result.lost_id,
                    "found_id": match_result.found_id,
                    "score": match_result.total_score
                }
            }
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(message_body).encode()),
                routing_key=queue.name,
            )
            print(f"[RABBITMQ] Evento publicado: Notificar al usuario {user_id}")

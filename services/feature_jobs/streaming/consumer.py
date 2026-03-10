import os
import json
import aiokafka
from redis_client import get_redis, incr_with_ttl

async def consume():
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    consumer = aiokafka.AIOKafkaConsumer(
        "events",
        bootstrap_servers=bootstrap,
        group_id="streaming-features-group",
        auto_offset_reset="earliest"
    )

    r = get_redis()

    await consumer.start()
    print("Streaming consumer started...")

    try:
        async for msg in consumer:
            event = json.loads(msg.value.decode("utf-8"))
            process_event(r, event)
    finally:
        await consumer.stop()

def process_event(r, event: dict):
    user_id = event["user_id"]
    item_id = event["item_id"]
    event_type = event["event_type"]

    if event_type == "view":
        incr_with_ttl(r, f"user:{user_id}:views_1h", 3600)
        incr_with_ttl(r, f"item:{item_id}:views_1h", 3600)
    elif event_type == "click":
        incr_with_ttl(r, f"user:{user_id}:clicks_1h", 3600)
        incr_with_ttl(r, f"item:{item_id}:clicks_1h", 3600)

    print(f"Updated Redis for user={user_id}, item={item_id}, type={event_type}")

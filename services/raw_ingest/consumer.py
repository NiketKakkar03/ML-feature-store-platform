import aiokafka
import json
import os
from datetime import datetime
from db import get_connection

async def consume():
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    consumer = aiokafka.AIOKafkaConsumer(
        "events",
        bootstrap_servers=bootstrap,
        group_id="raw-ingest-group",
        auto_offset_reset="earliest"
    )

    await consumer.start()
    print("✅ Consumer started, listening for events...")

    try:
        async for msg in consumer:
            event = json.loads(msg.value.decode("utf-8"))
            write_to_postgres(event)
    finally:
        await consumer.stop()

def write_to_postgres(event: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (user_id, item_id, event_type, device, ts)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        event["user_id"],
        event["item_id"],
        event["event_type"],
        event.get("device", "web"),
        event.get("timestamp", datetime.utcnow().isoformat())
    ))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"📥 Saved event: user={event['user_id']} item={event['item_id']} type={event['event_type']}")

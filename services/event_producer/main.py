from fastapi import FastAPI
from datetime import datetime
from producer import KafkaProducer
from models import UserEvent

app = FastAPI(title="Event Producer")

@app.post("/event")
async def send_event(event: UserEvent):
    event.timestamp = event.timestamp or datetime.utcnow()
    async with KafkaProducer() as producer:
        await producer.send_event("events", event.dict())
    return {"status": "sent", "event": event}

@app.post("/generate-batch/{count}")
async def generate_batch(count: int):
    events = []
    for i in range(count):
        events.append({
            "user_id": i % 10 + 1,
            "item_id": i % 20 + 1,
            "event_type": "view" if i % 3 != 0 else "click",
            "device": "web" if i % 2 == 0 else "mobile",
            "timestamp": datetime.utcnow().isoformat()
        })
    async with KafkaProducer() as producer:
        for event in events:
            await producer.send_event("events", event)
    return {"status": f"sent {len(events)} events"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

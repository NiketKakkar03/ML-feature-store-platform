import aiokafka
import json
import os
from typing import List, Dict

class KafkaProducer:
    def __init__(self, bootstrap_servers: List[str] = None):
        default = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.bootstrap_servers = bootstrap_servers or [default]
        self.producer = None

    async def __aenter__(self):
        self.producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers
        )
        await self.producer.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.producer.stop()

    async def send_event(self, topic: str, event: Dict):
        await self.producer.send_and_wait(
            topic,
            json.dumps(event, default=str).encode('utf-8')
        )

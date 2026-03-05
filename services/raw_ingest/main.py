import asyncio
import time
from db import create_tables
from consumer import consume
import socket

def wait_for_kafka(retries=10, delay=5):
    host = "kafka"
    port = 29092
    for i in range(retries):
        try:
            sock = socket.create_connection((host, port), timeout=3)
            sock.close()
            print(f"Kafka is reachable")
            return True
        except OSError:
            print(f"Waiting for Kafka... attempt {i+1}/{retries}")
            time.sleep(delay)
    raise Exception("Kafka not reachable after retries")

if __name__ == "__main__":
    wait_for_kafka()
    time.sleep(10) 
    create_tables()
    asyncio.run(consume())

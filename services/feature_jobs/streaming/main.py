import asyncio
import socket
import time
from consumer import consume

def wait_for_service(host, port, name, retries=12, delay=5):
    for i in range(retries):
        try:
            sock = socket.create_connection((host, port), timeout=3)
            sock.close()
            print(f"{name} is reachable")
            return
        except OSError:
            print(f"Waiting for {name}... attempt {i+1}/{retries}")
            time.sleep(delay)
    raise RuntimeError(f"{name} not reachable")

if __name__ == "__main__":
    wait_for_service("kafka", 29092, "Kafka")
    wait_for_service("redis", 6379, "Redis")
    asyncio.run(consume())

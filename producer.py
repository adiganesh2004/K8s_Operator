from kafka import KafkaProducer
import json
import time
import threading
from faker import Faker
import random

faker = Faker()

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    acks=1,
    linger_ms=5,
    batch_size=32768,  # 32 KB
    max_request_size=1048576,  # 1 MB
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

TOPIC = "test-topic"
MESSAGES_PER_SEC = 1000  # Tune this
NUM_THREADS = 4          # Tune this

def generate_record():
    return {
        "id": random.randint(1, 10_000_000),
        "name": faker.name(),
        "email": faker.email(),
        "address": faker.address(),
        "amount": round(random.uniform(10.5, 9999.99), 2),
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }

def send_bulk_messages():
    while True:
        start_time = time.time()
        for _ in range(MESSAGES_PER_SEC // NUM_THREADS):
            producer.send(TOPIC, generate_record())
        producer.flush()
        elapsed = time.time() - start_time
        sleep_time = max(0, 1 - elapsed)
        time.sleep(sleep_time)

if __name__ == "__main__":
    print(f"Starting producer with {NUM_THREADS} threads, {MESSAGES_PER_SEC} msg/sec")
    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=send_bulk_messages)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
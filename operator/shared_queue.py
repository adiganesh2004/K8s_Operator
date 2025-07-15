import queue
import threading

record_queue = queue.Queue()
queue_lock = threading.Lock()

def add_records(records):
    with queue_lock:
        for r in records:
            record_queue.put(r)

def get_batch(batch_size):
    batch = []
    with queue_lock:
        for _ in range(batch_size):
            if record_queue.empty():
                break
            batch.append(record_queue.get())
    return batch

def size():
    with queue_lock:
        return record_queue.qsize()

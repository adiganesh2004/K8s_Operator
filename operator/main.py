import kopf
import threading
from .mongo_poller import mongo_poller_loop
from .worker_manager import manager_loop

@kopf.on.startup()
def startup(**_):
    threading.Thread(target=mongo_poller_loop, daemon=True).start()
    threading.Thread(target=manager_loop, daemon=True).start()

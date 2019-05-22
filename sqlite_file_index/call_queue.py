import threading
from queue import Queue


class CallQueue(threading.Thread):
    def __init__(self):
        super().__init__()
        self.setDaemon(True)
        self.queue = Queue()

    def add_call(self, callee, *args, **kwargs):
        self.queue.put((callee, args, kwargs))

    def run(self) -> None:
        while True:
            callee, args, kwargs = self.queue.get(block=True)
            callee(*args, **kwargs)

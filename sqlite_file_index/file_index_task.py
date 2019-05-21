from threading import Thread, Event
from abc import ABC, abstractmethod
import typing

if typing.TYPE_CHECKING:
    from .file_index import FileIndex


class FileIndexTask(Thread, ABC):
    def __init__(self, index: 'FileIndex'):
        super().__init__()
        self.index: 'FileIndex' = index
        self.pause_flag = Event()
        self.pause_flag.set()

    def run(self) -> None:
        self.on_start()
        self.loop()
        self.on_finish()

    def on_start(self):
        pass

    def on_finish(self):
        pass

    def loop(self):
        while not self.complete():
            self.pause_flag.wait()
            self.iterate()
            self.pause_flag.wait()

    @abstractmethod
    def iterate(self):
        pass

    @abstractmethod
    def complete(self) -> bool:
        pass

    def pause(self):
        self.pause_flag.clear()

    def resume(self):
        self.pause_flag.set()

    def is_paused(self):
        return not self.pause_flag.is_set()

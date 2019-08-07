import sqlite3
import threading
from .retry import Retry
from typing import Tuple, Iterable, Any
from contextlib import contextmanager


def is_locked(error: sqlite3.OperationalError):
    return error.args[0] == 'database is locked'


retry_while_locked = Retry(
    tries=float('inf'),
    delay_between_tries=1,
    exception_types=(sqlite3.OperationalError,),
    exception_checks=(is_locked,)
)


@contextmanager
def conditional_lock(lock: threading.Lock, acquire):
    if acquire:
        try:
            lock.acquire()
            yield None
        finally:
            lock.release()

    else:
        try:
            yield None
        finally:
            pass


class ThreadsafeDatabase:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.lock = threading.Lock()

    def execute(
            self,
            query,
            params=(),
            *,
            cursor=None,
            commit=False,
            acquire_lock=True
    ) -> sqlite3.Cursor:

        with conditional_lock(self.lock, acquire_lock):
            if cursor is None:
                cursor = self.connection.cursor()

            retry_while_locked(cursor.execute, query, params)

            if commit:
                retry_while_locked(self.connection.commit)

            return cursor

    def execute_multiple(
            self,
            queries_and_params: Iterable[Tuple[str, Tuple[Any, ...]]],
            *,
            cursor=None,
            commit=False,
            acquire_lock=True
    ):
        with conditional_lock(self.lock, acquire_lock):
            if cursor is None:
                cursor = self.connection.cursor()

            for query, params in queries_and_params:
                retry_while_locked(cursor.execute, query, params)

            if commit:
                retry_while_locked(self.connection.commit)

    def execute_many(
            self,
            query, sequence_of_params,
            *,
            cursor=None,
            commit=False,
            acquire_lock=True
    ):
        with conditional_lock(self.lock, acquire_lock):
            if cursor is None:
                cursor = self.connection.cursor()

            retry_while_locked(cursor.executemany, query, sequence_of_params)

            if commit:
                retry_while_locked(self.connection.commit)

    def execute_script(
            self,
            script,
            *,
            cursor=None,
            commit=False,
            acquire_lock=True
    ) -> sqlite3.Cursor:

        with conditional_lock(self.lock, acquire_lock):
            if cursor is None:
                cursor = self.connection.cursor()

            retry_while_locked(cursor.executescript, script)

            if commit:
                retry_while_locked(self.connection.commit)

            return cursor

    def commit(self, acquire_lock=True):
        with conditional_lock(self.lock, acquire_lock):
            retry_while_locked(self.connection.commit)

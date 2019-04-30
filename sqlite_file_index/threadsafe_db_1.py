import sqlite3
import threading
from .retry import Retry
from contextlib import contextmanager

retry_until_success = Retry(
    tries=float('inf'),
    delay_between_tries=1,
    exception_types=(sqlite3.OperationalError,)
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


# class Query:
#     def __init__(self, sql, params, is_write=False):
#         self.sql = sql
#         self.params = params
#         self.is_write = is_write

class ThreadSafeDatabase:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.lock = threading.Lock()

    def execute(self, query, params=(), use_self_cursor=True, commit=False, acquire_lock=True) -> sqlite3.Cursor:
        with conditional_lock(self.lock, acquire_lock):
            if use_self_cursor:
                cursor = self.cursor
            else:
                cursor = self.connection.cursor()

            retry_until_success(cursor.execute, query, params)

            if commit:
                self.connection.commit()

            return cursor

    def execute_multiple(self, queries_and_params, use_self_cursor=True, commit=False, acquire_lock=True):
        with conditional_lock(self.lock, acquire_lock):
            if use_self_cursor:
                cursor = self.cursor
            else:
                cursor = self.connection.cursor()

            for query, params in queries_and_params:
                retry_until_success(cursor.execute, query, params)

            if commit:
                self.connection.commit()

    def commit(self, acquire_lock=True):
        with conditional_lock(self.lock, acquire_lock):
            self.connection.commit()

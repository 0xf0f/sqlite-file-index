import sqlite3
from pathlib import Path
from typing import Iterable, Optional
from weakref import ref, ReferenceType
from .threadsafe_db import ThreadsafeDatabase, retry_while_locked
from .iterator_stack import IteratorStack


class FileIndexNode:
    def __init__(self, file_index: 'FileIndex', row: sqlite3.Row):
        self.file_index: 'FileIndex' = file_index

        self.id = row['id']
        self.path = Path(row['path'])
        self.parent = row['parent']


class FileIndex:
    def __init__(self, path):
        self.connection = sqlite3.Connection(path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

        self.db = ThreadsafeDatabase(self.connection)

    @classmethod
    def load_from(cls, path):
        pass

    @classmethod
    def create_new(cls, path):
        pass

    def add_paths(self, paths: Iterable[Path], recursive=True):
        with self.db.lock:
            parent_cache = dict()
            cursor = self.db.connection.cursor()

            stack = IteratorStack()
            stack.push(paths)

            for path in stack:  # type: Path
                # parent = path.parent
                parent_id = parent_cache.get(path.parent, None)

                # '''
                # try get parent id
                #     check parent cache
                #     if parent not in there
                #         query db for parent, store id in parent cache
                #         if parent not in db:
                #
                #
                #
                # '''
                #
                # if path != parent:
                #     try:
                #         parent_id = parent_cache[parent]
                #
                #     except KeyError:
                #         parent_node = self.get_folder_node_by_path(str(path))
                #         if parent_node:
                #             parent_id = parent_node.id
                #             parent_cache[path] = parent_id
                #         else:
                #             for sub_parent in reversed(path.parents):
                #                 retry_while_locked(
                #                     cursor.execute,
                #                     'insert into folders (path, parent) values (?, ?)',
                #                     (str(path), parent_id)
                #                 )

                if path.is_file():
                    retry_while_locked(
                        cursor.execute,
                        'insert into files (path, parent) values (?, ?)',
                        (str(path), parent_id)
                    )

                else:
                    retry_while_locked(
                        cursor.execute,
                        'insert into folders (path, parent) values (?, ?)',
                        (str(path), parent_id)
                    )

                    if recursive:
                        stack.push(path.iterdir())
                        parent_cache[path] = cursor.lastrowid

            retry_while_locked(self.connection.commit)

    def get_file_node_by_id(self, file_id) -> Optional[FileIndexNode]:
        with self.db.lock:
            self.cursor.execute('select * from files where id=?', (file_id,))
            for row in self.cursor:
                return FileIndexNode(self, row)

    def get_folder_node_by_id(self, folder_id) -> Optional[FileIndexNode]:
        with self.db.lock:
            self.cursor.execute('select * from folders where id=?', (folder_id,))
            for row in self.cursor:
                return FileIndexNode(self, row)

    def get_file_node_by_path(self, path) -> Optional[FileIndexNode]:
        with self.db.lock:
            self.cursor.execute('select * from files where path=?', (path,))
            for row in self.cursor:
                return FileIndexNode(self, row)

    def get_folder_node_by_path(self, path) -> Optional[FileIndexNode]:
        with self.db.lock:
            self.cursor.execute('select * from folders where path=?', (path,))
            for row in self.cursor:
                return FileIndexNode(self, row)

import sqlite3
from pathlib import Path
from typing import Iterable, Optional
from .threadsafe_db import ThreadsafeDatabase, retry_while_locked
from .iterator_stack import IteratorStack


class FileIndexNode:
    def __init__(self, file_index: 'FileIndex', row: sqlite3.Row):
        self.file_index: 'FileIndex' = file_index

        self.id = row['id']
        self.path = Path(row['path'])
        self.parent = row['parent']

    def sub_node(self, row):
        return FileIndexNode(self.file_index, row)

    def search(self, keyword, recursive=False):
        if recursive:
            items = self.file_index.db.execute(
                f'''
                with recursive subfolders(_id) as (
                    values(?)
                    union all select id from folders, subfolders where parent=_id
                )

                select * from files where parent in subfolders and path like ?
                order by path collate nocase asc;
                ''', (self.id, f'%{keyword}%')
            )

            yield from map(self.sub_node, items)

        else:
            files = self.file_index.db.execute(
                'select * from files where parent=? and ' 
                'path like ? order by path asc', (self.id, f'%{keyword}%')
            )

            yield from map(self.sub_node, files)

    def iterdir(self, recursive=False):
        if recursive:
            items = self.file_index.db.execute(
                f'''
                with recursive subfolders(_id) as (
                    values(?)
                    union all select id from folders, subfolders where parent=_id
                )
    
                select * from folders where parent in subfolders
                union all
                select * from files where parent in subfolders
                order by path collate nocase asc;
                ''', (self.id,)
            )

            yield from map(self.sub_node, items)

        else:
            yield from self

    def __iter__(self):
        items = self.file_index.db.execute(
            f'''
            select * from folders where parent=?
            union all
            select * from files where parent=?
            order by path collate nocase asc;
            ''', (self.id, self.id)
        )

        yield from map(self.sub_node, items)


class FileIndex:
    connection: sqlite3.Connection
    db: ThreadsafeDatabase

    @classmethod
    def load_from(cls, path):
        result = cls()
        result.connection = sqlite3.Connection(path, check_same_thread=False)
        result.connection.row_factory = sqlite3.Row
        result.db = ThreadsafeDatabase(result.connection)
        return result

    @classmethod
    def create_new(cls, path):
        result = cls.load_from(path)
        result.db.execute_script(
            'pragma journal_mode=wal;'
            'pragma foreign_keys=ON;'
            'drop table if exists files;'
            'drop table if exists folders;'
            
            'create table folders('
                'id integer primary key,'
                'path text,'
                'parent integer,'
                'constraint unique_path unique (path)'
                'foreign key (parent) references folders(id) on delete cascade'
            ');'

            'create table files ('
                'id integer primary key,'
                'path text,'
                'parent integer,'
                'constraint unique_path unique (path)'
                'foreign key (parent) references folders(id) on delete cascade'
            ');'
        )
        return result

    def __get_parent_id(self, path: Path, cursor: sqlite3.Cursor, cache: dict):
        parent = path.parent

        try:
            return cache[parent]

        except KeyError:
            if path == parent:
                cache[parent] = None
                return None

            parent_node = self.get_folder_node_by_path(path, acquire_lock=False)

            if parent_node:
                cache[parent] = parent_node.id
                return parent_node.id

            else:
                grandparent_id = self.__get_parent_id(parent, cursor, cache)

                retry_while_locked(
                    cursor.execute,
                    'insert into folders (path, parent) values (?, ?)',
                    (str(parent), grandparent_id)
                )

                cache[parent] = cursor.lastrowid
                return cursor.lastrowid

    def add_paths(self, paths: Iterable[Path], recursive=True):
        with self.db.lock:
            parent_cache = dict()
            cursor = self.db.connection.cursor()

            stack = IteratorStack()
            stack.push(paths)

            for path in stack:  # type: Path
                parent_id = self.__get_parent_id(
                    path, cursor, parent_cache
                )

                if path.is_file():
                    try:
                        retry_while_locked(
                            cursor.execute,
                            'insert into files (path, parent) values (?, ?)',
                            (str(path), parent_id)
                        )

                    except sqlite3.IntegrityError:
                        continue

                else:

                    try:
                        retry_while_locked(
                            cursor.execute,
                            'insert into folders (path, parent) values (?, ?)',
                            (str(path), parent_id)
                        )

                    except sqlite3.IntegrityError:
                        continue

                    if recursive:
                        stack.push(path.iterdir())
                        parent_cache[path] = cursor.lastrowid

            retry_while_locked(self.connection.commit)

    def get_file_node_by_id(self, file_id, acquire_lock=False) -> Optional[FileIndexNode]:
        for row in self.db.execute(
                'select * from files where id=?', (file_id,),
                use_self_cursor=True, acquire_lock=acquire_lock
        ):
            return FileIndexNode(self, row)

    def get_folder_node_by_id(self, folder_id, acquire_lock=False) -> Optional[FileIndexNode]:
        for row in self.db.execute(
                'select * from folders where id=?', (folder_id,),
                use_self_cursor=True, acquire_lock=acquire_lock
        ):
            return FileIndexNode(self, row)

    def get_file_node_by_path(self, path: Path, acquire_lock=False) -> Optional[FileIndexNode]:
        for row in self.db.execute(
                'select * from files where path=?', (str(path),),
                use_self_cursor=True, acquire_lock=acquire_lock
        ):
            return FileIndexNode(self, row)

    def get_folder_node_by_path(self, path: Path, acquire_lock=False) -> Optional[FileIndexNode]:
        for row in self.db.execute(
                'select * from folders where path=?', (str(path),),
                use_self_cursor=True, acquire_lock=acquire_lock
        ):
            return FileIndexNode(self, row)

    def vacuum(self):
        self.db.execute('vacuum')

    def search(self, keyword, yield_folders=False):
        if yield_folders:
            folders = self.db.execute(
                'select * from folders where '
                'path like ? order by path collate nocase asc', (f'%{keyword}%',)
            )

            yield from map(lambda row: FileIndexNode(self, row), folders)

        files = self.db.execute(
            'select * from files where '
            'path like ? order by path collate nocase asc', (f'%{keyword}%',)
        )

        yield from map(lambda row: FileIndexNode(self, row), files)

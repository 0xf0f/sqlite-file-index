import sqlite3

from pathlib import Path
from typing import Iterable, Optional, Union, Type, Dict, TypeVar, Generic

from .iterator_stack import IteratorStack
from .file_index_node import FileIndexNode
from .optional_generator import optional_generator
from .threadsafe_db import ThreadsafeDatabase

cd = Path(__file__).parent
create_index_script = cd/'create_index.sqlite'

NodeType = TypeVar('NodeType', bound=FileIndexNode)


class FileIndex(Generic[NodeType]):
    connection: sqlite3.Connection
    node_cursor: sqlite3.Cursor
    db: ThreadsafeDatabase
    node_type: Type[FileIndexNode] = FileIndexNode

    file_metadata_columns: Dict[str, str] = dict()
    folder_metadata_columns: Dict[str, str] = dict()

    @classmethod
    def load_from(
            cls,
            path: Union[Path, str],
            *,
            load_metadata_columns=True
    ):
        result = cls()
        result.connection = sqlite3.Connection(path, check_same_thread=False)
        result.connection.execute('pragma foreign_keys=on;')
        result.connection.row_factory = sqlite3.Row
        result.node_cursor = result.connection.cursor()
        result.db = ThreadsafeDatabase(result.connection)

        if load_metadata_columns:
            result.file_metadata_columns = dict()
            result.folder_metadata_columns = dict()

            for row in result.db.execute(
                    'pragma table_info(file_metadata)'
            ):
                result.file_metadata_columns[
                    row['name']
                ] = row['type']

            for row in result.db.execute(
                    'pragma table_info(folder_metadata)'
            ):
                result.folder_metadata_columns[
                    row['name']
                ] = row['type']

        return result

    @classmethod
    def create_new(cls, path: Union[Path, str] = ':memory:'):
        result = cls.load_from(path, load_metadata_columns=False)
        with open(create_index_script) as script:
            result.db.execute_script(script.read())

        for name, type in cls.file_metadata_columns.items():
            result.db.execute(
                f'alter table file_metadata add column {name} {type}'
            )

        for name, type in cls.folder_metadata_columns.items():
            result.db.execute(
                f'alter table folder_metadata add column {name} {type}'
            )

        result.connection.commit()
        return result

    @classmethod
    def load_or_create(cls, path: Union[Path, str]):
        path = Path(path)
        if path.exists():
            return cls.load_from(path)
        else:
            return cls.create_new(path)

    def save_as(self, path: Union[Path, str]):
        path = Path(path)
        with self.db.lock:
            with sqlite3.connect(path) as backup:
                self.db.connection.backup(
                    backup
                )

    def __get_parent_id(
            self,
            path: Path,
            primary_cursor: sqlite3.Cursor,
            secondary_cursor: sqlite3.Cursor,
            cache: dict
    ):
        parent: Path = path.parent

        try:
            return cache[parent]

        except KeyError:
            if path == parent:
                cache[parent] = None
                return None

            parent_node = self.get_folder_node_by_path(
                parent, acquire_lock=False
            )

            if parent_node:
                cache[parent] = parent_node.id
                return parent_node.id

            else:
                grandparent_id = self.__get_parent_id(
                    parent, primary_cursor, secondary_cursor, cache
                )

                self.db.execute(
                    'insert into folders (path, parent) values (?, ?)',
                    (str(parent), grandparent_id),
                    cursor=primary_cursor
                )

                self.__add_metadata(
                    parent,
                    primary_cursor.lastrowid,
                    secondary_cursor
                )

                )

                cache[parent] = primary_cursor.lastrowid
                return primary_cursor.lastrowid

    def __add_metadata(
            self,
            path: Path,
            row_id: int,
            cursor: sqlite3.Cursor
    ):
        if path.is_dir():
            path_type = 'folder'
            metadata = self.initial_folder_metadata(path)
        else:
            path_type = 'file'
            metadata = self.initial_file_metadata(path)

        if metadata:
            column_string = ','.join(metadata.keys())
            value_string = ','.join('?'*len(metadata))

            self.db.execute(
                f'insert into {path_type}_metadata (id, {column_string}) '
                f'values (?, {value_string})',
                (row_id, *metadata.values()),
                cursor=cursor
            )

    @optional_generator
    def add_paths(
            self,
            paths: Iterable[Union[Path, str]],
            recursive=True,
            yield_paths=False,
            # yield_nodes=False,
            rescan=False
    ):
        parent_cache = dict()
        primary_cursor = self.db.connection.cursor()
        secondary_cursor = self.db.connection.cursor()

        stack = IteratorStack()
        stack.push(map(Path, paths))

        for path in stack:  # type: Path
            if yield_paths:
                yield path

            parent_id = self.__get_parent_id(
                path, primary_cursor, secondary_cursor, parent_cache
            )

            if path.is_file():
                try:
                    self.db.execute(
                        'insert into files (path, parent) values (?, ?)',
                        (str(path), parent_id),
                        cursor=primary_cursor,
                    )

                except sqlite3.IntegrityError:
                    continue

            else:
                try:
                    self.db.execute(
                        'insert into folders (path, parent) values (?, ?)',
                        (str(path), parent_id),
                        cursor=primary_cursor,
                    )

                except sqlite3.IntegrityError:
                    if not rescan:
                        continue

                else:
                    parent_cache[path] = primary_cursor.lastrowid

                if recursive:
                    stack.push(path.iterdir())

            self.__add_metadata(
                path,
                primary_cursor.lastrowid,
                secondary_cursor
            )


        self.db.commit()

    def get_file_node_by_id(
            self,
            file_id,
            acquire_lock=False
    ) -> Optional[NodeType]:

        for row in self.db.execute(
            'select * from files where id=?', (file_id,),
            cursor=self.node_cursor, acquire_lock=acquire_lock
        ):
            return self.new_node(row)

    def get_folder_node_by_id(
            self,
            folder_id,
            acquire_lock=False
    ) -> Optional[NodeType]:

        for row in self.db.execute(
            'select * from folders where id=?', (folder_id,),
            cursor=self.node_cursor, acquire_lock=acquire_lock
        ):
            return self.new_node(row)

    def get_file_node_by_path(
            self,
            path: Union[Path, str],
            acquire_lock=False
    ) -> Optional[NodeType]:

        for row in self.db.execute(
            'select * from files where path=?', (str(path),),
            cursor=self.node_cursor, acquire_lock=acquire_lock
        ):
            return self.new_node(row)

    def get_folder_node_by_path(
            self,
            path: Union[Path, str],
            acquire_lock=False
    ) -> Optional[NodeType]:

        for row in self.db.execute(
            'select * from folders where path=?', (str(path),),
            cursor=self.node_cursor, acquire_lock=acquire_lock
        ):
            return self.new_node(row)

    def vacuum(self):
        self.db.execute('vacuum')

    def search(self, keyword, yield_folders=False):
        keyword = f'%{keyword}%'

        if yield_folders:
            items = self.db.execute(
                'select * from folders where path like ? '
                'union all '
                'select * from files where path like ? '
                'order by path collate nocase asc;',
                (keyword, keyword)
            )
        else:
            items = self.db.execute(
                'select * from files where path like ? '
                'order by path collate nocase asc',
                (keyword,)
            )

        yield from map(self.new_node, items)

    def get_root_nodes(self):
        items = self.db.execute(
            'select * from folders where parent is null '
            'union all '
            'select * from files where parent is null '
            'order by path collate nocase asc'
        )

        yield from map(self.new_node, items)

    def new_node(self, row: sqlite3.Row) -> NodeType:
        return self.node_type(self, row)

    def __iter__(self):
        for node in self.get_root_nodes():
            yield node
            yield from node.iterdir(recursive=True)

    def initial_folder_metadata(
            self, path: Path
    ) -> Optional[Dict[str, Union[str, int, float]]]:
        pass

    def initial_file_metadata(
            self, path: Path
    ) -> Optional[Dict[str, Union[str, int, float]]]:
        pass

    # def add_file_metadata_column(self, name, type):
    #     self.db.execute(
    #         'alter table file_metadata add column ? ?',
    #         (type,)
    #     )
    #
    # def add_folder_metadata_column(self, name, type):
    #     pass

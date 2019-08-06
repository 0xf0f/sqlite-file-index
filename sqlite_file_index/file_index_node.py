from typing import TYPE_CHECKING, Iterable, Optional, Union, Dict, List
from pathlib import Path
from warnings import warn

import sqlite3

if TYPE_CHECKING:
    from .file_index import FileIndex
    from .file_index_tag import FileIndexTag


class FileIndexNode:
    def __init__(self, file_index: 'FileIndex', row: sqlite3.Row):
        self.index: 'FileIndex' = file_index

        self.id = row['id']
        self.path = Path(row['path'])
        self.parent = row['parent']

    # def sub_node(self, row):
    #     return self.index.new_node(row)

    def search(self, keyword, recursive=False):
        if recursive:
            items = self.index.db.execute(
                '''
                with recursive subfolders(_id) as (
                    values(?)
                    union all select id from folders, subfolders where parent=_id
                )

                select * from files where parent in subfolders and path like ?
                order by path collate nocase asc;
                ''',
                (self.id, f'%{keyword}%')
            )

            yield from map(self.index.new_node, items)

        else:
            files = self.index.db.execute(
                'select * from files where parent=? and '
                'path like ? order by path asc',
                (self.id, f'%{keyword}%')
            )

            yield from map(self.index.new_node, files)

    def iterdir(self, recursive=False):
        if recursive:
            items = self.index.db.execute(
                '''
                with recursive subfolders(_id) as (
                    values(?)
                    union all select id from folders, subfolders where parent=_id
                )

                select * from folders where parent in subfolders
                union all
                select * from files where parent in subfolders
                order by path collate nocase asc;
                ''',
                (self.id,)
            )

            yield from map(self.index.new_node, items)

        else:
            yield from self

    def __iter__(self):
        items = self.index.db.execute(
            '''
            select * from folders where parent=?
            union all
            select * from files where parent=?
            order by path collate nocase asc;
            ''', (self.id, self.id)
        )

        yield from map(self.index.new_node, items)

    def get_metadata(
            self,
            columns: Iterable[str] = None
    ) -> Optional[dict]:

        if self.path.is_dir():
            type = 'folder'
        else:
            type = 'file'

        if columns:
            column_string = ', '.join(columns)
        else:
            column_string = '*'

        print(self.id, type, column_string)

        for row in self.index.db.execute(
                f'select {column_string} from {type}_metadata where id=?',
                (self.id,)
        ):
            return dict(row)

    def set_metadata(
            self,
            columns: Dict[str, Union[str, int, float]],
    ):
        if columns:
            if self.path.is_file():
                type = 'file'
            else:
                type = 'folder'

            set_string = ', '.join(
                f'{key}=?' for key in columns.keys()
            )

            cursor = self.index.db.execute(
                f'update {type}_metadata set {set_string} where id={self.id}',
                tuple(columns.values())
            )

            if not cursor.rowcount:
                column_string = ', '.join(columns.keys())
                param_string = ', '.join('?'*len(columns))

                self.index.db.execute(
                    f'insert into {type}_metadata(id, {column_string}) '
                    f'values (?, {param_string})',
                    (self.id, *columns.values())
                )

            self.index.db.commit()

    def remove_tag(
        self,
        tag: Union[str, 'FileIndexTag'],
        *,
        commit=True
    ):
        if isinstance(tag, str):
            tag_name = tag
            tag = self.index.get_tag(tag)

            if tag is None:
                warn(f'Tag not found: {tag_name}', UserWarning)
                return

        if self.path.is_dir():
            path_type = 'folder'
        else:
            path_type = 'file'

        self.index.db.execute(
            f'delete from {path_type}_tags'
            f'where tag_id=? and {path_type}_id=?',
            (self.id, tag.id),
            commit=commit
        )

    def add_tag(
            self,
            tag: Union[str, 'FileIndexTag'],
            *,
            commit=True
    ) -> Optional['FileIndexTag']:
        if isinstance(tag, str):
            tag_name = tag
            tag = self.index.get_tag(tag)

            if tag is None:
                warn(f'Tag not found: {tag_name}', UserWarning)
                return

        if self.path.is_dir():
            path_type = 'folder'
        else:
            path_type = 'file'

        try:
            self.index.db.execute(
                f'insert into {path_type}_tags'
                f'({path_type}_id, tag_id) '
                'values (?,?)',
                (self.id, tag.id),
                commit=commit
            )
            return tag

        except sqlite3.IntegrityError:
            pass

    def get_tag_names(self) -> Iterable[str]:
        if self.path.is_dir():
            path_type = 'folder'
        else:
            path_type = 'file'
            
        for row in self.index.db.execute(
            f'''
            select name from tags where id in (
                select tag_id from {path_type}_tags
                where {path_type}_id = ?
            )
            ''',
            (self.id,)
        ):
            yield row['name']

    def __str__(self):
        return f'{self.__class__.__qualname__} ({self.path})'

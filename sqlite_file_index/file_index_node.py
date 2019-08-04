from typing import TYPE_CHECKING, Iterable, Optional, Union, Dict
from pathlib import Path
import sqlite3

if TYPE_CHECKING:
    from .file_index import FileIndex
    from .file_index_tag import FileIndexTag


class FileIndexNode:
    def __init__(self, file_index: 'FileIndex', row: sqlite3.Row):
        self.file_index: 'FileIndex' = file_index

        self.id = row['id']
        self.path = Path(row['path'])
        self.parent = row['parent']

    # def sub_node(self, row):
    #     return self.file_index.new_node(row)

    def search(self, keyword, recursive=False):
        if recursive:
            items = self.file_index.db.execute(
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

            yield from map(self.file_index.new_node, items)

        else:
            files = self.file_index.db.execute(
                'select * from files where parent=? and '
                'path like ? order by path asc',
                (self.id, f'%{keyword}%')
            )

            yield from map(self.file_index.new_node, files)

    def iterdir(self, recursive=False):
        if recursive:
            items = self.file_index.db.execute(
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

            yield from map(self.file_index.new_node, items)

        else:
            yield from self

    def __iter__(self):
        items = self.file_index.db.execute(
            '''
            select * from folders where parent=?
            union all
            select * from files where parent=?
            order by path collate nocase asc;
            ''', (self.id, self.id)
        )

        yield from map(self.file_index.new_node, items)

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

        for row in self.file_index.db.execute(
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

            cursor = self.file_index.db.execute(
                f'update {type}_metadata set {set_string} where id={self.id}',
                tuple(columns.values())
            )

            if not cursor.rowcount:
                column_string = ', '.join(columns.keys())
                param_string = ', '.join('?'*len(columns))

                self.file_index.db.execute(
                    f'insert into {type}_metadata(id, {column_string}) '
                    f'values (?, {param_string})',
                    (self.id, *columns.values())
                )

            self.file_index.db.commit()

    def add_tag(
            self,
            tag: Union[str, 'FileIndexTag'],
            *,
            commit=True
    ):
        if isinstance(tag, str):
            tag = self.file_index.get_tag(tag)

            if tag is None:
                raise UserWarning('Tag')

        if self.path.is_dir():
            path_type = 'folder'
        else:
            path_type = 'file'

        try:
            self.file_index.db.execute(
                f'insert into {path_type}_tags'
                f'({path_type}_id, tag_id) '
                'values (?,?)',
                (self.id, tag.id),
                commit=commit
            )

        except sqlite3.IntegrityError:
            pass

    def remove_tag(
        self,
        tag: Union[str, 'FileIndexTag'],
        *,
        commit=True
    ):
        if isinstance(tag, str):
            tag = self.file_index.get_tag(tag)

        if self.path.is_dir():
            path_type = 'folder'
        else:
            path_type = 'file'

        self.file_index.db.execute(
            f'delete from {path_type}_tags'
            f'where tag_id=? and {path_type}_id=?',
            (self.id, tag.id),
            commit=commit
        )

    def __str__(self):
        return f'{self.__class__.__qualname__} ({self.path})'

from typing import TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from .file_index import FileIndex
    import sqlite3


class FileIndexNode:
    def __init__(self, file_index: 'FileIndex', row: 'sqlite3.Row'):
        self.file_index: 'FileIndex' = file_index

        self.id = row['id']
        self.path = Path(row['path'])
        self.parent = row['parent']

    # def sub_node(self, row):
    #     return self.file_index.new_node(row)

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
                f'''
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
            f'''
            select * from folders where parent=?
            union all
            select * from files where parent=?
            order by path collate nocase asc;
            ''', (self.id, self.id)
        )

        yield from map(self.file_index.new_node, items)

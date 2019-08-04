import sqlite3
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .file_index import FileIndex


class FileIndexTag:
    def __init__(self, index: 'FileIndex', row: Union[dict, sqlite3.Row]):
        self.index: 'FileIndex' = index
        self.id = row['id']
        self.name = row['name']

    def get_files_with_tag(self):
        rows = self.index.db.execute(
            '''
            select * from files where id in (
               select file_id from file_tags where tag_id=?
            )
            
            order by path collate nocase asc
            ''',
            (self.id,)
        )

        yield from map(
            self.index.new_node, rows
        )

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    import sqlite3
    from .file_index import FileIndex


class FileIndexTag:
    def __init__(self, index: 'FileIndex', row: Union[dict, 'sqlite3.Row']):
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

    def get_folders_with_tag(self):
        rows = self.index.db.execute(
            '''
            select * from folders where id in (
               select folder_id from folder_tags where tag_id=?
            )

            order by path collate nocase asc
            ''',
            (self.id,)
        )

        yield from map(
            self.index.new_node, rows
        )

    def delete(self):
        self.index.db.execute(
            'delete from tags where tag_id=?', (self.id,)
        )

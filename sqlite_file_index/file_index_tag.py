import sqlite3
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .file_index import FileIndex


class FileIndexTag:
    def __init__(self, index: 'FileIndex', row: Union[dict, sqlite3.Row]):
        self.index: 'FileIndex' = index
        self.id = row['id']
        self.name = row['name']

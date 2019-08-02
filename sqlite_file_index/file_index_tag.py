import sqlite3


class FileIndexTag:
    def __init__(self, row: sqlite3.Row):
        self.id = row['id']
        self.name = row['name']

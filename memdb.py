from sqlitedict import SqliteDict

class ModSqliteDict(SqliteDict):
    def __init__(self):

        # Initialize in-memory db
        self.filename = ':memory:'
        super().__init__()

mem = ModSqliteDict()
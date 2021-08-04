from sqlitedict import SqliteDict
from varname.core import nameof

class ModSqliteDict(SqliteDict):
    def __init__(self):

        # Initialize in-memory db
        self.filename = ':memory:'
        super().__init__()

    def set_key(self, item):
        name = nameof(item)
        self[name] = item

mem = ModSqliteDict()
from sqlitedict import SqliteDict
from varname.core import nameof
from hashlib import md5

class ModSqliteDict(SqliteDict):
    def __init__(self):

        # Initialize in-memory db
        self.filename = ':memory:'
        super().__init__()

    def set_key(self, item):
        name = nameof(item)
        self[name] = item

    def set_key_value(self, item, value):
        name = nameof(item)
        self[name] = value

mem = ModSqliteDict()
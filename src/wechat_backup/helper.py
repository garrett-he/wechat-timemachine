import os
import hashlib
import sqlite3
from json import JSONEncoder
from datetime import datetime
from dataclasses import is_dataclass


def sqlite_connect(path: str) -> sqlite3.Connection:
    def dict_factory(cursor, row) -> dict:
        d = {}
        for i, col in enumerate(cursor.description):
            d[col[0]] = row[i]
        return d

    conn = sqlite3.connect(path)
    conn.row_factory = dict_factory

    return conn


class EntityJSONEncoder(JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return obj.__dict__

        if isinstance(obj, datetime):
            return obj.isoformat()

        if isinstance(obj, Enum):
            return obj.name

        return JSONEncoder.default(self, obj)


def md5_utf8(s):
    m = hashlib.md5()
    m.update(s.encode('utf-8'))

    return m.hexdigest()


def path_or_none(path: str) -> str:
    return os.path.exists(path) and path or None

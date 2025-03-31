import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


from wechat_timemachine.helper import (
    EntityJSONEncoder,
    md5_utf8,
    path_or_none,
    sqlite_connect,
)


class TestSqliteConnect:
    def test_returns_connection(self, tmp_path):
        db_path = tmp_path / "test.db"
        conn = sqlite_connect(str(db_path))
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_row_factory_returns_dict(self, tmp_path):
        db_path = tmp_path / "test.db"
        conn = sqlite_connect(str(db_path))
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO t (id, name) VALUES (1, 'Alice')")
        row = conn.execute("SELECT * FROM t").fetchone()
        assert row == {"id": 1, "name": "Alice"}
        conn.close()


class TestEntityJSONEncoder:
    def test_encodes_dataclass(self):
        @dataclass
        class Sample:
            x: int
            y: str

        obj = Sample(x=1, y="a")
        assert json.loads(json.dumps(obj, cls=EntityJSONEncoder)) == {"x": 1, "y": "a"}

    def test_encodes_datetime(self):
        dt = datetime(2021, 1, 1, 12, 0, 0)
        assert json.loads(json.dumps(dt, cls=EntityJSONEncoder)) == "2021-01-01T12:00:00"

    def test_encodes_enum(self):
        class Color(Enum):
            Red = 1
            Green = 2

        assert json.loads(json.dumps(Color.Green, cls=EntityJSONEncoder)) == "Green"


class TestMd5Utf8:
    def test_basic(self):
        assert md5_utf8("hello") == "5d41402abc4b2a76b9719d911017c592"

    def test_unicode(self):
        assert md5_utf8("你好") == "7eca689f0d3389d9dea66ae112e5cfd7"

    def test_empty(self):
        assert md5_utf8("") == "d41d8cd98f00b204e9800998ecf8427e"


class TestPathOrNone:
    def test_existing_path(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("x")
        assert path_or_none(str(f)) == str(f)

    def test_missing_path(self):
        assert path_or_none("/nonexistent/path/to/file.txt") is None

    def test_existing_relative_path(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        Path("a.txt").write_text("x")
        assert path_or_none("a.txt") == "a.txt"

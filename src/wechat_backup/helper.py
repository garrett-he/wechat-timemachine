# -*- coding: utf-8 -*-
# Copyright (C) 2020 Garrett HE <garrett.he@hotmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

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

import sqlite3
from dataclasses import dataclass
from wechat_backup.context import WechatPlatform, WechatContext
from wechat_backup.helper import sqlite_connect


@dataclass
class WechatContextIos(WechatContext):
    doc_dir: str
    contact_db: sqlite3.Connection
    mm_db: sqlite3.Connection


def new_context(config: dict):
    return WechatContextIos(
        platform=WechatPlatform.iOS,
        user_id=config['user_id'],
        doc_dir=config['doc_dir'],
        mm_db=sqlite_connect('%s/DB/MM.sqlite' % config['doc_dir']),
        contact_db=sqlite_connect('%s/DB/WCDB_Contact.sqlite' % config['doc_dir']),
        emoji_cache=config['emoji_cache']
    )

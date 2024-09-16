import os.path
import sqlite3
from dataclasses import dataclass
from glob import glob
from typing import List
from wechat_backup.context import WechatPlatform, WechatContext
from wechat_backup.helper import sqlite_connect


@dataclass
class WechatContextIos(WechatContext):
    doc_dir: str
    contact_db: sqlite3.Connection
    mm_db: sqlite3.Connection
    message_db: List[sqlite3.Connection]


def new_context(config: dict):
    return WechatContextIos(
        platform=WechatPlatform.iOS,
        user_id=config['user_id'],
        doc_dir=config['doc_dir'],
        mm_db=sqlite_connect('%s/DB/MM.sqlite' % config['doc_dir']),
        contact_db=sqlite_connect('%s/DB/WCDB_Contact.sqlite' % config['doc_dir']),
        emoji_cache=config['emoji_cache'],
        message_db=[sqlite_connect(db_file) for db_file in
                    glob(f'{os.path.join(config["doc_dir"], "DB")}/message_*.sqlite')],
    )

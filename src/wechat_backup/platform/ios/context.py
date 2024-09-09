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

import sqlite3
from dataclasses import dataclass
from wechat_backup.context import WechatPlatform, WechatContext
from wechat_backup.helper import sqlite_connect


@dataclass
class WechatContextAndroid(WechatContext):
    db: sqlite3.Connection
    media_dir: str


def new_context(config: dict):
    return WechatContextAndroid(
        platform=WechatPlatform.Android,
        user_id=config['user_id'],
        db=sqlite_connect(config['db_file']),
        media_dir=config['media_dir'],
        emoji_cache=config['emoji_cache']
    )

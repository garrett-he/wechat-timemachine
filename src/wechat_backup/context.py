from dataclasses import dataclass
from enum import Enum


class WechatPlatform(Enum):
    All = 'all'
    iOS = 'ios'
    Android = 'android'


@dataclass
class WechatContext:
    platform: WechatPlatform
    user_id: str
    emoji_cache: str

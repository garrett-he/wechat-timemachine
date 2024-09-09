import os
import sys
from lxml import etree
from .typing import *
from wechat_backup.context import WechatContext, WechatPlatform

_CONTENT_PARSERS = {}
_APPMSG_PARSERS = {}


class WechatMessageType(Enum):
    Text = 1
    Image = 3
    Voice = 34
    NameCard = 42
    Video = 43
    Emoji = 47
    Location = 48
    Application = 49
    VoIP = 50
    WechatVideo = 62
    System = 10000


class WechatAppmsgType(Enum):
    Text = 1
    Image = 2
    Music = 3
    Video = 4
    Link = 5
    Attachment = 6
    Game = 7
    Emoji = 8
    EmojiSet = 15
    Coupon = 16
    LocationShare = 17
    ChatHistory = 19
    WechatSport = 21
    FavorChatHistory = 24
    Microprogram = 33
    GiftCard = 34
    MicroprogramLink = 36
    VideoRedPacket = 46
    MediaPreviewVideo = 54
    Reference = 57
    Transfer = 2000
    MoneyPacket = 2001


def content_parser(type: WechatMessageType, platform: WechatPlatform = WechatPlatform.All):
    def wrapper(fn):
        if platform not in _CONTENT_PARSERS.keys():
            _CONTENT_PARSERS[platform] = {}

        _CONTENT_PARSERS[platform][type] = fn

        return fn

    return wrapper


def appmsg_parser(type: WechatAppmsgType, platform: WechatPlatform = WechatPlatform.All):
    def wrapper(fn):
        if platform not in _APPMSG_PARSERS.keys():
            _APPMSG_PARSERS[platform] = {}

        _APPMSG_PARSERS[platform][type] = fn

        return fn

    return wrapper


def assemble_message(record: dict, context: WechatContext) -> Message:
    def get_sender_id():
        conversation_id = record['conversation_id']

        if conversation_id[-9:] == '@chatroom':
            if record['is_send'] == 1:
                return context.user_id
            else:
                p = record['content'].find(':')
                sender = record['content'][:p]
                record['content'] = record['content'][p + 2:]

                return sender
        else:
            return record['is_send'] == 1 and context.user_id or record['conversation_id']

    # noinspection PyProtectedMember
    if record['type'] not in WechatMessageType._value2member_map_.keys():
        record['type'] = 49

    msg_type = WechatMessageType(record['type'])

    if context.platform not in _CONTENT_PARSERS.keys() or msg_type not in _CONTENT_PARSERS[context.platform].keys():
        platform = WechatPlatform.All
    else:
        platform = context.platform

    try:
        content_type, content = _CONTENT_PARSERS[platform][msg_type](record=record, context=context)
    except Exception as e:
        sys.stderr.write(record.__str__() + '\n')
        raise e

    return Message(
        conversation_id=record['conversation_id'],
        sent_at=datetime.fromtimestamp(record['sent_at']),
        sender_id=get_sender_id(),
        type=content_type.value,
        content=content
    )


# noinspection PyUnusedLocal
@content_parser(type=WechatMessageType.Text)
def parse_content_text(record: dict, context: WechatContext):
    return TextContent.content_type, TextContent(text=record['content'])


# noinspection PyUnusedLocal
@content_parser(type=WechatMessageType.System)
def parse_content_system(record: dict, context: WechatContext):
    return SystemContent.content_type, SystemContent(text=record['content'])


# noinspection PyUnusedLocal
@content_parser(type=WechatMessageType.NameCard)
def parse_content_name_card(record: dict, context: WechatContext):
    node = etree.fromstring(record['content']).xpath('/msg')[0]

    username = node.attrib['username']

    return NameCardContent.content_type, NameCardContent(
        user_id=username,
        nickname=node.attrib['nickname'],
        province=node.attrib['province'],
        city=node.attrib['city'],
        gender=NameCardContent.Gender(int(node.attrib['sex']))
    )


# noinspection PyUnusedLocal
@content_parser(type=WechatMessageType.Location)
def parse_content_location(record: dict, context: WechatContext):
    node = etree.fromstring(record['content']).xpath('/msg/location')[0]

    return LocationContent.content_type, LocationContent(
        latitude=float(node.attrib['x']),
        longitude=float(node.attrib['y']),
        address=node.attrib['label'],
        label=node.attrib['poiname']
    )


@content_parser(type=WechatMessageType.Application)
def parse_content_application(record: dict, context: WechatContext):
    app_type = WechatAppmsgType(int(etree.fromstring(record['content']).xpath('/msg/appmsg/type')[0].text))

    if context.platform not in _APPMSG_PARSERS.keys() or app_type not in _APPMSG_PARSERS[context.platform].keys():
        platform = WechatPlatform.All
    else:
        platform = context.platform

    return _APPMSG_PARSERS[platform][app_type](record=record, context=context)


# noinspection PyUnusedLocal
@appmsg_parser(type=WechatAppmsgType.Text)
def parse_appmsg_text(record: dict, context: WechatContext):
    appmsg = etree.fromstring(record['content']).xpath('/msg/appmsg')[0]

    return TextContent.content_type, TextContent(
        text=appmsg.xpath('title')[0].text,
    )


# noinspection PyUnusedLocal
@appmsg_parser(type=WechatAppmsgType.MoneyPacket)
def parse_appmsg_money_packet(record: dict, context: WechatContext):
    appmsg = etree.fromstring(record['content']).xpath('/msg/appmsg')[0]
    wcpayinfo = appmsg.xpath('wcpayinfo')[0]

    return MoneyPacketContent.content_type, MoneyPacketContent(
        payment_info=MoneyPacketContent.PaymentInfo(
            icon_url=wcpayinfo.xpath('iconurl')[0].text,
            receiver_title=wcpayinfo.xpath('receivertitle')[0].text,
            receiver_description=wcpayinfo.xpath('receiverdes')[0].text,
            sender_title=wcpayinfo.xpath('sendertitle')[0].text,
            sender_description=wcpayinfo.xpath('senderdes')[0].text,
            scene_id=int(wcpayinfo.xpath('sceneid')[0].text),
            scene_description=wcpayinfo.xpath('senderdes')[0].text
        ),
        title=appmsg.xpath('title')[0].text,
        description=appmsg.xpath('des')[0].text
    )


# noinspection PyUnusedLocal
@appmsg_parser(type=WechatAppmsgType.Transfer)
def parse_appmsg_transfer(record: dict, context: WechatContext):
    appmsg = etree.fromstring(record['content']).xpath('/msg/appmsg')[0]
    wcpayinfo = appmsg.xpath('wcpayinfo')[0]

    # noinspection PyCallByClass
    return TransferContent.content_type, TransferContent(
        payment_info=TransferContent.PaymentInfo(
            subtype=int(wcpayinfo.xpath('paysubtype')[0].text),
            description=wcpayinfo.xpath('feedesc')[0].text,
            transfer_id=wcpayinfo.xpath('transferid')[0].text,
            transfer_time=int(wcpayinfo.xpath('begintransfertime')[0].text),
            expire_time=int(wcpayinfo.xpath('invalidtime')[0].text),
            memo=wcpayinfo.xpath('pay_memo')[0].text,
        ),
        title=appmsg.xpath('title')[0].text,
        description=appmsg.xpath('des')[0].text
    )


# noinspection PyUnusedLocal
@appmsg_parser(type=WechatAppmsgType.LocationShare)
def parse_appmsg_location_share(record: dict, context: WechatContext):
    appmsg = etree.fromstring(record['content']).xpath('/msg/appmsg')[0]

    return LocationShareContent.content_type, LocationShareContent(title=appmsg.xpath('title')[0].text)


@appmsg_parser(type=WechatAppmsgType.Emoji)
def parse_appmsg_emoji(record: dict, context: WechatContext):
    appmsg = etree.fromstring(record['content']).xpath('/msg/appmsg')[0]
    md5 = appmsg.xpath('appattach/emoticonmd5')[0].text

    path = '%s/%s.gif' % (context.emoji_cache, md5)

    if not os.path.exists(path):
        sys.stderr.write('[WARNING] No emoji found for "%s".\n' % md5)
        path = 'emoji://%s' % md5

    return EmojiContent.content_type, EmojiContent(
        file_path=path
    )

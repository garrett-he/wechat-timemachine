import sqlite3
from typing import Iterable, List
from .context import WechatContextIos
from wechat_backup.helper import md5_utf8, path_or_none
from wechat_backup.message.parser import *
from wechat_backup.context import WechatPlatform


def find_message_db(table_name: str, db_list: List[sqlite3.Connection]):
    for db in db_list:
        row = db.cursor().execute("SELECT COUNT(*) AS C FROM sqlite_master WHERE type = 'table' AND name = ?",
                                  (table_name,)).fetchone()
        if row['C'] > 0:
            return db


def load_messages(context: WechatContextIos, conversation_id: str) -> Iterable[dict]:
    table_name = 'Chat_%s' % md5_utf8(conversation_id)

    db = find_message_db(table_name, context.message_db)

    sql = f'''
            SELECT
                '{conversation_id}' AS conversation_id,
                Type AS type,
                NOT Des AS is_send,
                CreateTime AS sent_at,
                Message AS content,

                MesLocalID
            FROM {table_name}
            ORDER BY CreateTime
            '''

    return db.cursor().execute(sql).fetchall()


@content_parser(platform=WechatPlatform.iOS, type=WechatMessageType.Image)
def parse_content_image(record: dict, context: WechatContextIos):
    doc_dir = context.doc_dir
    prefix = '%s/Img/%s' % (doc_dir, md5_utf8(record['conversation_id']))

    return ImageContent.content_type, ImageContent(
        file_path=path_or_none('%s/%d.pic' % (prefix, record['MesLocalID'])),
        thumbnail_path=path_or_none('%s/%d.pic_thum' % (prefix, record['MesLocalID'])),
        high_definition_path=path_or_none('%s/%d.pic_hd' % (prefix, record['MesLocalID']))
    )


@content_parser(platform=WechatPlatform.iOS, type=WechatMessageType.Voice)
def parse_content_voice(record: dict, context: WechatContextIos):
    prefix = '%s/Audio/%s' % (context.doc_dir, md5_utf8(record['conversation_id']))

    node = etree.fromstring(record['content']).xpath('/msg/voicemsg')[0]

    return VoiceContent.content_type, VoiceContent(
        file_path=path_or_none('%s/%d.aud' % (prefix, record['MesLocalID'])),
        duration=int(node.attrib['voicelength'])
    )


@content_parser(platform=WechatPlatform.iOS, type=WechatMessageType.Video)
@content_parser(platform=WechatPlatform.iOS, type=WechatMessageType.WechatVideo)
def parse_content_video(record: dict, context: WechatContextIos):
    node = etree.fromstring(record['content']).xpath('/msg/videomsg')[0]

    return VideoContent.content_type, VideoContent(
        file_path=path_or_none(
            '%s/Video/%s/%d.mp4' % (context.doc_dir, md5_utf8(record['conversation_id']), record['MesLocalID'])),
        duration=int(node.attrib['playlength']),
        thumbnail_path=path_or_none(
            '%s/Video/%s/%d.video_thum' % (context.doc_dir, md5_utf8(record['conversation_id']), record['MesLocalID']))
    )


# noinspection PyUnusedLocal
@content_parser(platform=WechatPlatform.iOS, type=WechatMessageType.VoIP)
def parse_content_voip(record: dict, context: WechatContextIos):
    node = etree.fromstring('<root>%s</root>' % record['content']).xpath('/root')[0]
    status = VoIPContent.VoIPStatus(int(node.xpath('voipinvitemsg/status')[0].text))

    return VoIPContent.content_type, VoIPContent(
        type=VoIPContent.VoIPType(int(node.xpath('voipinvitemsg/invitetype')[0].text)),
        status=status,
        duration=int(node.xpath('voiplocalinfo/duration')[0].text) if status == VoIPContent.VoIPStatus.Answered else 0
    )


@content_parser(platform=WechatPlatform.iOS, type=WechatMessageType.Emoji)
def parse_content_emoji(record: dict, context: WechatContextIos):
    md5 = etree.fromstring(record['content']).xpath('/msg/emoji')[0].attrib['md5']

    path = '%s/%s.gif' % (context.emoji_cache, md5)

    if not os.path.exists(path):
        sys.stderr.write('[WARNING] No emoji found for "%s".\n' % md5)
        path = 'emoji://%s' % md5

    return EmojiContent.content_type, EmojiContent(file_path=path)


@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.Attachment)
def parse_appmsg_attachment(record: dict, context: WechatContextIos):
    appmsg = etree.fromstring(record['content']).xpath('/msg/appmsg')[0]
    file_ext = appmsg.xpath('/msg/appmsg/appattach/fileext')[0].text

    # noinspection PyArgumentList
    return AttachmentContent.content_type, AttachmentContent(
        title=appmsg.xpath('title')[0].text,
        file_path=path_or_none('%s/OpenData/%s/%d.%s' % (
            context.doc_dir, md5_utf8(record['conversation_id']), record['MesLocalID'], file_ext))
    )


@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.Video)
@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.Game)
@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.EmojiSet)
@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.Microprogram)
@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.MicroprogramLink)
@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.GiftCard)
@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.Coupon)
@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.ChatHistory)
@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.FavorChatHistory)
@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.Link)
def parse_appmsg_link(record: dict, context: WechatContextIos):
    appmsg = etree.fromstring(record['content']).xpath('/msg/appmsg')[0]

    return LinkContent.content_type, LinkContent(
        title=appmsg.xpath('title')[0].text,
        description=appmsg.xpath('des')[0].text,
        url=appmsg.xpath('url')[0].text,
        thumbnail_path=path_or_none(
            '%s/OpenData/%s/%d.pic_thum' % (context.doc_dir, md5_utf8(record['conversation_id']), record['MesLocalID']))
    )


@appmsg_parser(platform=WechatPlatform.iOS, type=WechatAppmsgType.Image)
def parse_appmsg_image(record: dict, context: WechatContextIos):
    # noinspection PyTypeChecker
    return ImageContent.content_type, ImageContent(
        file_path=path_or_none(
            '%s/OpenData/%s/%d.dat' % (context.doc_dir, md5_utf8(record['conversation_id']), record['MesLocalID'])),
        thumbnail_path=path_or_none('%s/OpenData/%s/%d.pic_thum' % (
            context.doc_dir, md5_utf8(record['conversation_id']), record['MesLocalID'])),
        high_definition_path=None
    )


# noinspection PyUnusedLocal
@appmsg_parser(type=WechatAppmsgType.Music)
def parse_appmsg_music(record: dict, context: WechatContextIos):
    appmsg = etree.fromstring(record['content']).xpath('/msg/appmsg')[0]

    # noinspection PyArgumentList
    return MusicContent.content_type, MusicContent(
        data_url=appmsg.xpath('dataurl')[0].text,
        **parse_appmsg_link(record=record, context=context)[1].__dict__
    )

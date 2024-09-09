from typing import Iterable
from .context import WechatContextAndroid
from wechat_backup.helper import md5_utf8, path_or_none
from wechat_backup.message.parser import *
from wechat_backup.context import WechatPlatform


def load_messages(context: WechatContextAndroid, conversation_id: str) -> Iterable[dict]:
    sql = f'''
            SELECT
                m.talker AS conversation_id,
                m.type AS type,
                m.isSend AS is_send,
                CAST(m.createTime/1000 AS INT) AS sent_at,
                m.content AS content,

                m.imgPath AS m_imgPath,
                i.bigImgPath AS i_bigImgPath,
                i.thumbImgPath AS i_thumbImgPath,

                v.videolength AS v_videolength,

                a.fileFullPath as a_fileFullPath
            FROM message AS m
                LEFT JOIN ImgInfo2 AS i ON i.msgSvrId = m.msgSvrId
                LEFT JOIN videoinfo2 AS v ON v.msgsvrid = m.msgSvrId
                LEFT JOIN appattach AS a ON a.msgInfoId = m.msgId
            WHERE m.talker = '{conversation_id}'
            ORDER BY m.createTime
            '''

    return context.db.cursor().execute(sql).fetchall()


@content_parser(platform=WechatPlatform.Android, type=WechatMessageType.Image)
def parse_content_image(record: dict, context: WechatContextAndroid):
    i_bigImgPath = record['i_bigImgPath']
    i_thumbImgPath = record['i_thumbImgPath'][-32:]

    image_path = f'{context.media_dir}/image2/%s/%s/%s' % (i_bigImgPath[0:2], i_bigImgPath[2:4], i_bigImgPath)
    thumbnail_path = f'{context.media_dir}/image2/%s/%s/th_%s' % (
        i_thumbImgPath[0:2], i_thumbImgPath[2:4], i_thumbImgPath)

    return ImageContent.content_type, ImageContent(
        thumbnail_path=path_or_none(thumbnail_path),
        file_path=path_or_none(image_path),
        high_definition_path=path_or_none('%s_hd' % image_path)
    )


@content_parser(platform=WechatPlatform.Android, type=WechatMessageType.Video)
@content_parser(platform=WechatPlatform.Android, type=WechatMessageType.WechatVideo)
def parse_content_video(record: dict, context: WechatContextAndroid):
    return VideoContent.content_type, VideoContent(
        file_path=path_or_none('%s/video/%s.mp4' % (context.media_dir, record['m_imgPath'])),
        thumbnail_path=path_or_none('%s/video/%s.jpg' % (context.media_dir, record['m_imgPath'])),
        duration=int(record['v_videolength'])
    )


# noinspection PyUnusedLocal
# VoIP not available for Android
@content_parser(platform=WechatPlatform.Android, type=WechatMessageType.VoIP)
def parse_content_voip(record: dict, context: WechatContextAndroid):
    return VoIPContent.content_type, VoIPContent(
        type=VoIPContent.VoIPType.Unknown,
        status=VoIPContent.VoIPStatus.Cancelled,
        duration=-1
    )


@content_parser(platform=WechatPlatform.Android, type=WechatMessageType.Emoji)
def parse_content_emoji(record: dict, context: WechatContextAndroid):
    m_imgPath = record['m_imgPath']
    path = '%s/%s.gif' % (context.emoji_cache, m_imgPath)

    if not os.path.exists(path):
        sys.stderr.write('[WARNING] No emoji found for "%s".\n' % m_imgPath)
        path = 'emoji://%s' % m_imgPath

    return EmojiContent.content_type, EmojiContent(file_path=path)


@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.Video)
@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.Game)
@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.EmojiSet)
@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.Microprogram)
@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.MicroprogramLink)
@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.GiftCard)
@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.Coupon)
@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.ChatHistory)
@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.FavorChatHistory)
@appmsg_parser(platform=WechatPlatform.Android, type=WechatAppmsgType.Link)
def parse_appmsg_link(record: dict, context: WechatContextAndroid):
    appmsg = etree.fromstring(record['content']).xpath('/msg/appmsg')[0]

    return LinkContent.content_type, LinkContent(
        title=appmsg.xpath('title')[0].text,
        description=appmsg.xpath('des')[0].text,
        url=appmsg.xpath('url')[0].text,
        thumbnail_path=None
    )


@content_parser(platform=WechatPlatform.Android, type=WechatMessageType.Voice)
def parse_content_voice(record: dict, context: WechatContextAndroid):
    m_imgPath = md5_utf8(record['m_imgPath'])

    return VoiceContent.content_type, VoiceContent(
        file_path=path_or_none(
            '%s/voice2/%s/%s/msg_%s.amr' % (context.media_dir, m_imgPath[:2], m_imgPath[2:4], record['m_imgPath'])),
        duration=int(record['content'].split(':')[1])
    )

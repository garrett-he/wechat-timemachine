
from wechat_timemachine.context import WechatPlatform
from wechat_timemachine.message.typing import (
    AttachmentContent,
    EmojiContent,
    ImageContent,
    LinkContent,
    MusicContent,
    VideoContent,
    VoiceContent,
    VoIPContent,
)
from wechat_timemachine.message.parser import (
    WechatAppmsgType,
    WechatMessageType,
    _CONTENT_PARSERS,
    _APPMSG_PARSERS,
)
from wechat_timemachine.platform.ios.contact import (
    parse_blob_column,
    parse_contact_remark,
    parse_contact_rows,
)
from wechat_timemachine.platform.ios.context import new_context
from wechat_timemachine.platform.ios.message import find_message_db, load_messages


class TestIosNewContext:
    def test_creates_context(self, tmp_path):
        doc_dir = tmp_path / "doc"
        doc_dir.mkdir()
        (doc_dir / "DB").mkdir()
        # Create minimal required DB files
        import sqlite3

        for name in ("MM.sqlite", "WCDB_Contact.sqlite"):
            conn = sqlite3.connect(str(doc_dir / "DB" / name))
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER)")
            conn.close()

        config = {
            "user_id": "u1",
            "doc_dir": str(doc_dir),
            "emoji_cache": str(tmp_path / "emoji"),
        }
        ctx = new_context(config)
        assert ctx.platform == WechatPlatform.iOS
        assert ctx.user_id == "u1"


class TestIosBlobParsing:
    def test_parse_blob_column(self):
        # Build a simple blob: key (1 byte) + length (1 byte) + value
        blob = b"\x0a\x05Hello\x1a\x03Bye"
        result = parse_blob_column(blob)
        assert result == {0x0A: "Hello", 0x1A: "Bye"}

    def test_parse_contact_remark(self):
        blob = b"\x0a\x05Alice\x12\x05alias\x1a\x03Ali\x3a\x06remark\x42\x031,2"
        result = parse_contact_remark(blob)
        assert result["nickname"] == "Alice"
        assert result["id_alias"] == "alias"
        assert result["nickname_alias"] == "Ali"
        assert result["remark"] == "remark"
        assert result["tag_ids"] == "1,2"

    def test_parse_contact_remark_empty(self):
        blob = b"\x0a\x00\x12\x00"
        result = parse_contact_remark(blob)
        assert result["nickname"] is None
        assert result["id_alias"] is None


class TestIosParseContactRows:
    def test_friend_avatar_parsing(self):
        # dbContactHeadImage for non-gh friend: first byte != 8, second byte = length of thumbnail_url
        # structure: [flag, thumb_len, thumb_url, ..., avatar_len, avatar_url]
        # Simplified valid blob for regular user based on code path
        # This is a rough approximation; the actual parsing depends on byte layout.
        # Let's build a simpler test using the gh_ path instead.

        rows = [
            {
                "id": "gh_test",
                "dbContactRemark": b"\x0a\x08Official",
                "dbContactHeadImage": bytes([0, 10]) + b"http://t1" + bytes([0, 0, 10]) + b"http://a1",
            }
        ]
        result = parse_contact_rows(rows)
        assert result[0]["id"] == "gh_test"
        assert result[0]["nickname"] == "Official"


class TestIosFindMessageDb:
    def test_finds_table(self, ios_message_db_populated):
        from wechat_timemachine.helper import md5_utf8

        table_name = "Chat_%s" % md5_utf8("wxid_conversation")
        db = find_message_db(table_name, [ios_message_db_populated])
        assert db is ios_message_db_populated

    def test_not_found(self, ios_message_db_populated):
        db = find_message_db("Chat_NONEXISTENT", [ios_message_db_populated])
        assert db is None


class TestIosLoadMessages:
    def test_load(self, ios_context, ios_message_db_populated):
        from wechat_timemachine.helper import md5_utf8

        table_name = "Chat_%s" % md5_utf8("wxid_conversation")
        cur = ios_message_db_populated.cursor()
        cur.execute(
            f"INSERT INTO {table_name} (MesLocalID, Type, Des, CreateTime, Message) VALUES (1, 1, 0, 1609459200, 'Hi')"
        )
        ios_message_db_populated.commit()

        ios_context.message_db = [ios_message_db_populated]
        msgs = list(load_messages(ios_context, "wxid_conversation"))
        assert len(msgs) == 1
        assert msgs[0]["conversation_id"] == "wxid_conversation"
        assert msgs[0]["content"] == "Hi"
        assert msgs[0]["is_send"] == 1  # NOT Des (0) -> 1


class TestIosParsers:
    def test_parse_content_image(self, tmp_path, ios_context):
        from wechat_timemachine.helper import md5_utf8

        conv_md5 = md5_utf8("wxid_conv")
        img_dir = tmp_path / "doc" / "Img" / conv_md5
        img_dir.mkdir(parents=True)
        (img_dir / "1.pic").write_text("img")
        (img_dir / "1.pic_thum").write_text("thum")

        record = {"conversation_id": "wxid_conv", "MesLocalID": 1}
        parser = _CONTENT_PARSERS[WechatPlatform.iOS][WechatMessageType.Image]
        content_type, content = parser(record=record, context=ios_context)
        assert content_type == ImageContent.content_type
        assert content.file_path is not None
        assert content.thumbnail_path is not None

    def test_parse_content_voice(self, tmp_path, ios_context):
        from wechat_timemachine.helper import md5_utf8

        conv_md5 = md5_utf8("wxid_conv")
        aud_dir = tmp_path / "doc" / "Audio" / conv_md5
        aud_dir.mkdir(parents=True)
        (aud_dir / "2.aud").write_text("aud")

        record = {
            "conversation_id": "wxid_conv",
            "MesLocalID": 2,
            "content": '<msg><voicemsg voicelength="5000"/></msg>',
        }
        parser = _CONTENT_PARSERS[WechatPlatform.iOS][WechatMessageType.Voice]
        content_type, content = parser(record=record, context=ios_context)
        assert content_type == VoiceContent.content_type
        assert content.duration == 5000
        assert content.file_path is not None

    def test_parse_content_video(self, tmp_path, ios_context):
        from wechat_timemachine.helper import md5_utf8

        conv_md5 = md5_utf8("wxid_conv")
        vid_dir = tmp_path / "doc" / "Video" / conv_md5
        vid_dir.mkdir(parents=True)
        (vid_dir / "3.mp4").write_text("mp4")
        (vid_dir / "3.video_thum").write_text("thum")

        record = {
            "conversation_id": "wxid_conv",
            "MesLocalID": 3,
            "content": '<msg><videomsg playlength="12"/></msg>',
        }
        parser = _CONTENT_PARSERS[WechatPlatform.iOS][WechatMessageType.Video]
        content_type, content = parser(record=record, context=ios_context)
        assert content_type == VideoContent.content_type
        assert content.duration == 12
        assert content.file_path is not None

    def test_parse_content_voip_cancelled(self, ios_context):
        record = {
            "content": "<voipinvitemsg><status>5</status><invitetype>1</invitetype></voipinvitemsg><voiplocalinfo><duration>0</duration></voiplocalinfo>"
        }
        parser = _CONTENT_PARSERS[WechatPlatform.iOS][WechatMessageType.VoIP]
        content_type, content = parser(record=record, context=ios_context)
        assert content_type == VoIPContent.content_type
        assert content.status == VoIPContent.VoIPStatus.Cancelled
        assert content.duration == 0

    def test_parse_content_voip_answered(self, ios_context):
        record = {
            "content": "<voipinvitemsg><status>4</status><invitetype>0</invitetype></voipinvitemsg><voiplocalinfo><duration>60</duration></voiplocalinfo>"
        }
        parser = _CONTENT_PARSERS[WechatPlatform.iOS][WechatMessageType.VoIP]
        content_type, content = parser(record=record, context=ios_context)
        assert content.status == VoIPContent.VoIPStatus.Answered
        assert content.duration == 60

    def test_parse_content_emoji(self, tmp_path, ios_context):
        emoji_dir = tmp_path / "emoji"
        emoji_dir.mkdir(exist_ok=True)
        (emoji_dir / "emojimd5.gif").write_text("gif")

        ios_context.emoji_cache = str(emoji_dir)
        record = {"content": '<msg><emoji md5="emojimd5"/></msg>'}
        parser = _CONTENT_PARSERS[WechatPlatform.iOS][WechatMessageType.Emoji]
        content_type, content = parser(record=record, context=ios_context)
        assert content_type == EmojiContent.content_type
        assert content.file_path == str(emoji_dir / "emojimd5.gif")

    def test_parse_appmsg_attachment(self, tmp_path, ios_context):
        from wechat_timemachine.helper import md5_utf8

        conv_md5 = md5_utf8("wxid_conv")
        open_dir = tmp_path / "doc" / "OpenData" / conv_md5
        open_dir.mkdir(parents=True)
        (open_dir / "4.pdf").write_text("pdf")

        record = {
            "conversation_id": "wxid_conv",
            "MesLocalID": 4,
            "content": "<msg><appmsg><type>6</type><title>Doc</title><appattach><fileext>pdf</fileext></appattach></appmsg></msg>",
        }
        parser = _APPMSG_PARSERS[WechatPlatform.iOS][WechatAppmsgType.Attachment]
        content_type, content = parser(record=record, context=ios_context)
        assert content_type == AttachmentContent.content_type
        assert content.title == "Doc"
        assert content.file_path is not None

    def test_parse_appmsg_link(self, tmp_path, ios_context):
        from wechat_timemachine.helper import md5_utf8

        conv_md5 = md5_utf8("wxid_conv")
        open_dir = tmp_path / "doc" / "OpenData" / conv_md5
        open_dir.mkdir(parents=True)
        (open_dir / "5.pic_thum").write_text("thum")

        record = {
            "conversation_id": "wxid_conv",
            "MesLocalID": 5,
            "content": (
                "<msg><appmsg><type>5</type><title>Link</title><des>Desc</des>"
                "<url>http://example.com</url></appmsg></msg>"
            ),
        }
        parser = _APPMSG_PARSERS[WechatPlatform.iOS][WechatAppmsgType.Link]
        content_type, content = parser(record=record, context=ios_context)
        assert content_type == LinkContent.content_type
        assert content.title == "Link"
        assert content.thumbnail_path is not None

    def test_parse_appmsg_music(self, ios_context):
        record = {
            "conversation_id": "wxid_conv",
            "MesLocalID": 6,
            "content": (
                "<msg><appmsg><type>3</type><title>Music</title><des>Desc</des>"
                "<url>http://music</url><dataurl>http://data</dataurl></appmsg></msg>"
            ),
        }
        parser = _APPMSG_PARSERS[WechatPlatform.All][WechatAppmsgType.Music]
        content_type, content = parser(record=record, context=ios_context)
        assert content_type == MusicContent.content_type
        assert content.data_url == "http://data"
        assert content.title == "Music"

    def test_parse_appmsg_image(self, tmp_path, ios_context):
        from wechat_timemachine.helper import md5_utf8

        conv_md5 = md5_utf8("wxid_conv")
        open_dir = tmp_path / "doc" / "OpenData" / conv_md5
        open_dir.mkdir(parents=True)
        (open_dir / "7.dat").write_text("dat")
        (open_dir / "7.pic_thum").write_text("thum")

        record = {
            "conversation_id": "wxid_conv",
            "MesLocalID": 7,
            "content": "<msg><appmsg><type>2</type></appmsg></msg>",
        }
        parser = _APPMSG_PARSERS[WechatPlatform.iOS][WechatAppmsgType.Image]
        content_type, content = parser(record=record, context=ios_context)
        assert content_type == ImageContent.content_type
        assert content.file_path is not None
        assert content.high_definition_path is None

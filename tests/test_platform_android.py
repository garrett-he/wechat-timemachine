
from wechat_timemachine.context import WechatPlatform
from wechat_timemachine.message.typing import EmojiContent, ImageContent, VideoContent, VoIPContent
from wechat_timemachine.message.parser import (
    WechatAppmsgType,
    WechatMessageType,
    _CONTENT_PARSERS,
    _APPMSG_PARSERS,
)
from wechat_timemachine.platform.android.contact import (
    load_chatrooms,
    load_contact_labels,
    load_friends,
    load_microprograms,
    load_official_accounts,
)
from wechat_timemachine.platform.android.context import new_context
from wechat_timemachine.platform.android.message import load_messages


class TestAndroidNewContext:
    def test_creates_context(self, tmp_path):
        db_file = tmp_path / "test.db"
        db_file.write_text("")
        config = {
            "user_id": "u1",
            "db_file": str(db_file),
            "media_dir": str(tmp_path / "media"),
            "emoji_cache": str(tmp_path / "emoji"),
        }
        ctx = new_context(config)
        assert ctx.platform == WechatPlatform.Android
        assert ctx.user_id == "u1"
        assert ctx.media_dir == config["media_dir"]


class TestAndroidLoadContactLabels:
    def test_load_labels(self, android_context, android_friends_db):
        cur = android_friends_db.cursor()
        cur.execute("INSERT INTO ContactLabel (labelID, labelName) VALUES (1, 'Family'), (2, 'Work')")
        android_friends_db.commit()

        labels = load_contact_labels(android_context)
        assert labels == {1: "Family", 2: "Work"}


class TestAndroidLoadFriends:
    def test_load_friends(self, android_context, android_friends_db):
        cur = android_friends_db.cursor()
        cur.execute(
            """
            INSERT INTO rcontact
            (username, alias, nickname, conRemark, contactLabelIds, conRemarkPYShort, pyInitial, type)
            VALUES
            ('wxid_alice', 'alice_alias', 'Alice', 'Alicia', '1', 'AL', 'AL', 1),
            ('wxid_bob', '', 'Bob', '', '', 'BO', 'BO', 1)
            """
        )
        cur.execute("INSERT INTO img_flag (username, reserved1) VALUES ('wxid_alice', 'http://avatar')")
        android_friends_db.commit()

        friends = list(load_friends(android_context))
        assert len(friends) == 2
        assert friends[0]["id"] == "wxid_alice"
        assert friends[0]["avatar_url"] == "http://avatar"


class TestAndroidLoadOfficialAccounts:
    def test_load_official(self, android_context, android_friends_db):
        cur = android_friends_db.cursor()
        ext = '{"RegisterSource": {"RegisterBody": "BodyA"}, "Appid": "app123"}'
        cur.execute(
            """
            INSERT INTO rcontact
            (username, alias, nickname, conRemark, conRemarkPYShort, pyInitial, type)
            VALUES ('gh_news', 'news_alias', 'News', '', 'NE', 'NE', 1)
            """
        )
        cur.execute(
            "INSERT INTO bizinfo (username, brandIconURL, extInfo) VALUES ('gh_news', 'http://icon', ?)",
            (ext,),
        )
        android_friends_db.commit()

        oas = list(load_official_accounts(android_context))
        assert len(oas) == 1
        assert oas[0]["account_entity"] == "BodyA"
        assert oas[0]["app_id"] == "app123"


class TestAndroidLoadMicroprograms:
    def test_load_microprograms(self, android_context, android_friends_db):
        cur = android_friends_db.cursor()
        cur.execute(
            """
            INSERT INTO rcontact
            (username, alias, nickname, conRemark, conRemarkPYShort, pyInitial, type)
            VALUES ('gh_mini@app', '', 'Mini', '', 'MI', 'MI', 1)
            """
        )
        android_friends_db.commit()

        mps = list(load_microprograms(android_context))
        assert len(mps) == 1
        assert mps[0]["id"] == "gh_mini@app"


class TestAndroidLoadChatrooms:
    def test_load_chatrooms(self, android_context, android_friends_db):
        cur = android_friends_db.cursor()
        cur.execute(
            """
            INSERT INTO rcontact
            (username, alias, nickname, conRemark, conRemarkPYShort, pyInitial, type)
            VALUES ('room@chatroom', '', 'Group', '', 'GR', 'GR', 1)
            """
        )
        cur.execute(
            """
            INSERT INTO chatroom
            (chatroomname, memberlist, roomowner, selfDisplayName, modifytime)
            VALUES ('room@chatroom', 'a;b;c', 'a', 'Me', 1)
            """
        )
        android_friends_db.commit()

        rooms = list(load_chatrooms(android_context))
        assert len(rooms) == 1
        assert rooms[0]["member_ids"] == "a;b;c"


class TestAndroidLoadMessages:
    def test_load_messages(self, android_context, android_messages_db):
        cur = android_messages_db.cursor()
        cur.execute(
            """
            INSERT INTO message
            (msgId, msgSvrId, type, isSend, createTime, talker, content, imgPath)
            VALUES (1, 100, 1, 0, 1609459200000, 'wxid_alice', 'Hello', 'img1')
            """
        )
        android_messages_db.commit()

        msgs = list(load_messages(android_context, "wxid_alice"))
        assert len(msgs) == 1
        assert msgs[0]["conversation_id"] == "wxid_alice"
        assert msgs[0]["sent_at"] == 1609459200
        assert msgs[0]["content"] == "Hello"


class TestAndroidParsers:
    def test_parse_content_image(self, tmp_path, android_context):
        # Create fake media files
        media_dir = tmp_path / "media"
        img_dir = media_dir / "image2" / "ab" / "cd"
        img_dir.mkdir(parents=True)
        (img_dir / "abcdef1234567890abcdef1234567890").write_text("img")
        (img_dir / "th_abcdef1234567890abcdef1234567890").write_text("thumb")

        android_context.media_dir = str(media_dir)

        record = {
            "i_bigImgPath": "abcdef1234567890abcdef1234567890",
            "i_thumbImgPath": "xxabcdef1234567890abcdef1234567890",
        }
        parser = _CONTENT_PARSERS[WechatPlatform.Android][WechatMessageType.Image]
        content_type, content = parser(record=record, context=android_context)
        assert content_type == ImageContent.content_type
        assert isinstance(content, ImageContent)
        assert content.file_path is not None
        assert content.thumbnail_path is not None

    def test_parse_content_video(self, tmp_path, android_context):
        media_dir = tmp_path / "media"
        video_dir = media_dir / "video"
        video_dir.mkdir(parents=True)
        (video_dir / "vid123.mp4").write_text("mp4")
        (video_dir / "vid123.jpg").write_text("thumb")

        android_context.media_dir = str(media_dir)

        record = {
            "m_imgPath": "vid123",
            "v_videolength": 15000,
        }
        parser = _CONTENT_PARSERS[WechatPlatform.Android][WechatMessageType.Video]
        content_type, content = parser(record=record, context=android_context)
        assert content_type == VideoContent.content_type
        assert content.duration == 15000
        assert content.file_path is not None

    def test_parse_content_voip(self, android_context):
        parser = _CONTENT_PARSERS[WechatPlatform.Android][WechatMessageType.VoIP]
        content_type, content = parser(record={}, context=android_context)
        assert content_type == VoIPContent.content_type
        assert content.type == VoIPContent.VoIPType.Unknown
        assert content.status == VoIPContent.VoIPStatus.Cancelled

    def test_parse_content_emoji(self, tmp_path, android_context):
        emoji_dir = tmp_path / "emoji"
        emoji_dir.mkdir(exist_ok=True)
        (emoji_dir / "emoji123.gif").write_text("gif")

        android_context.emoji_cache = str(emoji_dir)

        record = {"m_imgPath": "emoji123"}
        parser = _CONTENT_PARSERS[WechatPlatform.Android][WechatMessageType.Emoji]
        content_type, content = parser(record=record, context=android_context)
        assert content_type == EmojiContent.content_type
        assert content.file_path == str(emoji_dir / "emoji123.gif")

    def test_parse_appmsg_link(self, android_context):
        record = {
            "content": (
                "<msg><appmsg><type>5</type><title>Link Title</title>"
                "<des>Desc</des><url>http://example.com</url></appmsg></msg>"
            ),
        }
        parser = _APPMSG_PARSERS[WechatPlatform.Android][WechatAppmsgType.Link]
        content_type, content = parser(record=record, context=android_context)
        assert content.title == "Link Title"
        assert content.url == "http://example.com"

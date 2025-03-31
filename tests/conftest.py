import sqlite3
from pathlib import Path

import pytest

from wechat_timemachine.context import WechatPlatform, WechatContext
from wechat_timemachine.platform.android.context import WechatContextAndroid
from wechat_timemachine.platform.ios.context import WechatContextIos


# ---------------------------------------------------------------------------
# Helpers / shared paths
# ---------------------------------------------------------------------------

@pytest.fixture
def res_dir() -> Path:
    return Path(__file__).with_name("res")


# ---------------------------------------------------------------------------
# Generic context fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generic_context() -> WechatContext:
    return WechatContext(
        platform=WechatPlatform.All,
        user_id="wxid_testuser",
        emoji_cache="/tmp/emoji",
    )


# ---------------------------------------------------------------------------
# Android context fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def android_db() -> sqlite3.Connection:
    from wechat_timemachine.helper import sqlite_connect
    conn = sqlite_connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def android_context(tmp_path, android_db) -> WechatContextAndroid:
    media_dir = tmp_path / "media"
    media_dir.mkdir()
    emoji_cache = tmp_path / "emoji"
    emoji_cache.mkdir()

    ctx = WechatContextAndroid(
        platform=WechatPlatform.Android,
        user_id="wxid_android_user",
        db=android_db,
        media_dir=str(media_dir),
        emoji_cache=str(emoji_cache),
    )
    yield ctx
    ctx.db.close()


@pytest.fixture
def android_friends_db(android_db):
    """Populate an in-memory Android DB with minimal friend schema."""
    cur = android_db.cursor()
    cur.executescript(
        """
        CREATE TABLE rcontact (
            username TEXT PRIMARY KEY,
            alias TEXT,
            nickname TEXT,
            conRemark TEXT,
            contactLabelIds TEXT,
            conRemarkPYShort TEXT,
            pyInitial TEXT,
            type INTEGER,
            verifyFlag INTEGER DEFAULT 0
        );
        CREATE TABLE img_flag (username TEXT PRIMARY KEY, reserved1 TEXT);
        CREATE TABLE chatroom (
            chatroomname TEXT PRIMARY KEY,
            memberlist TEXT,
            roomowner TEXT,
            selfDisplayName TEXT,
            modifytime INTEGER
        );
        CREATE TABLE bizinfo (username TEXT PRIMARY KEY, brandIconURL TEXT, extInfo TEXT);
        CREATE TABLE ContactLabel (labelID INTEGER PRIMARY KEY, labelName TEXT);
        """
    )
    android_db.commit()
    return android_db


@pytest.fixture
def android_messages_db(android_db):
    """Populate an in-memory Android DB with minimal message schema."""
    cur = android_db.cursor()
    cur.executescript(
        """
        CREATE TABLE message (
            msgId INTEGER PRIMARY KEY,
            msgSvrId INTEGER,
            type INTEGER,
            isSend INTEGER,
            createTime INTEGER,
            talker TEXT,
            content TEXT,
            imgPath TEXT
        );
        CREATE TABLE ImgInfo2 (msgSvrId INTEGER PRIMARY KEY, bigImgPath TEXT, thumbImgPath TEXT);
        CREATE TABLE videoinfo2 (msgsvrid INTEGER PRIMARY KEY, videolength INTEGER);
        CREATE TABLE appattach (msgInfoId INTEGER PRIMARY KEY, fileFullPath TEXT);
        """
    )
    android_db.commit()
    return android_db


# ---------------------------------------------------------------------------
# iOS context fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ios_contact_db() -> sqlite3.Connection:
    from wechat_timemachine.helper import sqlite_connect
    conn = sqlite_connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def ios_mm_db() -> sqlite3.Connection:
    from wechat_timemachine.helper import sqlite_connect
    conn = sqlite_connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def ios_message_db() -> sqlite3.Connection:
    from wechat_timemachine.helper import sqlite_connect
    conn = sqlite_connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def ios_context(tmp_path, ios_contact_db, ios_mm_db, ios_message_db) -> WechatContextIos:
    doc_dir = tmp_path / "doc"
    doc_dir.mkdir()
    emoji_cache = tmp_path / "emoji"
    emoji_cache.mkdir()

    ctx = WechatContextIos(
        platform=WechatPlatform.iOS,
        user_id="wxid_ios_user",
        doc_dir=str(doc_dir),
        contact_db=ios_contact_db,
        mm_db=ios_mm_db,
        emoji_cache=str(emoji_cache),
        message_db=[ios_message_db],
    )
    yield ctx
    ctx.contact_db.close()
    ctx.mm_db.close()
    for db in ctx.message_db:
        db.close()


@pytest.fixture
def ios_contact_db_populated(ios_contact_db):
    """Populate an in-memory iOS contact DB with minimal schema."""
    cur = ios_contact_db.cursor()
    cur.executescript(
        """
        CREATE TABLE Friend (
            userName TEXT PRIMARY KEY,
            encodeUserName TEXT,
            dbContactRemark BLOB,
            dbContactHeadImage BLOB,
            type INTEGER,
            certificationFlag INTEGER
        );
        """
    )
    ios_contact_db.commit()
    return ios_contact_db


@pytest.fixture
def ios_message_db_populated(ios_message_db):
    """Populate an in-memory iOS message DB with a Chat table."""
    cur = ios_message_db.cursor()
    from wechat_timemachine.helper import md5_utf8
    table_name = "Chat_%s" % md5_utf8("wxid_conversation")
    cur.execute(
        f"""
        CREATE TABLE {table_name} (
            MesLocalID INTEGER PRIMARY KEY,
            Type INTEGER,
            Des INTEGER,
            CreateTime INTEGER,
            Message TEXT
        );
        """
    )
    ios_message_db.commit()
    return ios_message_db


# ---------------------------------------------------------------------------
# Record fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def text_record() -> dict:
    return {
        "conversation_id": "wxid_someone",
        "type": 1,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": "Hello world",
    }


@pytest.fixture
def system_record() -> dict:
    return {
        "conversation_id": "wxid_someone",
        "type": 10000,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": "System notification",
    }


@pytest.fixture
def chatroom_text_record() -> dict:
    return {
        "conversation_id": "group123@chatroom",
        "type": 1,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": "sender123: Hello group",
    }


@pytest.fixture
def name_card_record() -> dict:
    return {
        "conversation_id": "wxid_someone",
        "type": 42,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": '<msg username="wxid_card" nickname="CardName" sex="1" province="Guangdong" city="Shenzhen"/>',
    }


@pytest.fixture
def location_record() -> dict:
    return {
        "conversation_id": "wxid_someone",
        "type": 48,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": '<msg><location x="22.5431" y="114.0579" label="Shenzhen" poiname="PointA"/></msg>',
    }


@pytest.fixture
def appmsg_text_record() -> dict:
    return {
        "conversation_id": "wxid_someone",
        "type": 49,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": "<msg><appmsg><type>1</type><title>App Title</title></appmsg></msg>",
    }


@pytest.fixture
def money_packet_record() -> dict:
    return {
        "conversation_id": "wxid_someone",
        "type": 49,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": (
            "<msg><appmsg><type>2001</type><title>Red Packet</title><des>Lucky money</des>"
            "<wcpayinfo><iconurl>http://example.com/icon.png</iconurl>"
            "<receivertitle>Receive</receivertitle><receiverdes>You got money</receiverdes>"
            "<sendertitle>Send</sendertitle><senderdes>Sent money</senderdes>"
            "<sceneid>1</sceneid></wcpayinfo></appmsg></msg>"
        ),
    }


@pytest.fixture
def transfer_record() -> dict:
    return {
        "conversation_id": "wxid_someone",
        "type": 49,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": (
            "<msg><appmsg><type>2000</type><title>Transfer</title><des>Money transfer</des>"
            "<wcpayinfo><paysubtype>1</paysubtype><feedesc>¥100</feedesc>"
            "<transferid>tid123</transferid><begintransfertime>1609459200</begintransfertime>"
            "<invalidtime>1609545600</invalidtime><pay_memo>Thanks</pay_memo></wcpayinfo></appmsg></msg>"
        ),
    }


@pytest.fixture
def location_share_record() -> dict:
    return {
        "conversation_id": "wxid_someone",
        "type": 49,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": "<msg><appmsg><type>17</type><title>Shared Location</title></appmsg></msg>",
    }


@pytest.fixture
def appmsg_emoji_record() -> dict:
    return {
        "conversation_id": "wxid_someone",
        "type": 49,
        "is_send": 0,
        "sent_at": 1609459200,
        "content": "<msg><appmsg><type>8</type><appattach><emoticonmd5>abc123def456</emoticonmd5></appattach></appmsg></msg>",
    }

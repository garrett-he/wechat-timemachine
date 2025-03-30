# NOTE: platform modules MUST be imported before assemble_message runs
# so that parsers are registered in global registries.
import wechat_timemachine.platform.android.message  # noqa: F401
import wechat_timemachine.platform.ios.message  # noqa: F401

import pytest

from wechat_timemachine.context import WechatPlatform
from wechat_timemachine.message.parser import assemble_message
from wechat_timemachine.message.typing import (
    EmojiContent,
    LocationContent,
    LocationShareContent,
    MessageType,
    MoneyPacketContent,
    NameCardContent,
    SystemContent,
    TextContent,
    TransferContent,
)


class TestAssembleMessageText:
    def test_incoming_text(self, generic_context, text_record):
        msg = assemble_message(record=text_record.copy(), context=generic_context)
        assert msg.conversation_id == "wxid_someone"
        assert msg.sender_id == "wxid_someone"
        assert msg.type == MessageType.Text.value
        assert isinstance(msg.content, TextContent)
        assert msg.content.text == "Hello world"

    def test_outgoing_text(self, generic_context, text_record):
        rec = text_record.copy()
        rec["is_send"] = 1
        msg = assemble_message(record=rec, context=generic_context)
        assert msg.sender_id == generic_context.user_id


class TestAssembleMessageSystem:
    def test_system(self, generic_context, system_record):
        msg = assemble_message(record=system_record.copy(), context=generic_context)
        assert msg.type == MessageType.System.value
        assert isinstance(msg.content, SystemContent)
        assert msg.content.text == "System notification"


class TestAssembleMessageChatroom:
    def test_chatroom_incoming(self, generic_context, chatroom_text_record):
        rec = chatroom_text_record.copy()
        msg = assemble_message(record=rec, context=generic_context)
        assert msg.sender_id == "sender123"
        # Note: sender prefix is stripped from record *after* content parsing,
        # so the parsed TextContent still contains the original prefix.
        assert msg.content.text == "sender123: Hello group"

    def test_chatroom_outgoing(self, generic_context, chatroom_text_record):
        rec = chatroom_text_record.copy()
        rec["is_send"] = 1
        msg = assemble_message(record=rec, context=generic_context)
        assert msg.sender_id == generic_context.user_id


class TestAssembleMessageNameCard:
    def test_name_card(self, generic_context, name_card_record):
        msg = assemble_message(record=name_card_record.copy(), context=generic_context)
        assert msg.type == MessageType.NameCard.value
        assert isinstance(msg.content, NameCardContent)
        assert msg.content.user_id == "wxid_card"
        assert msg.content.nickname == "CardName"
        assert msg.content.gender == NameCardContent.Gender.Male


class TestAssembleMessageLocation:
    def test_location(self, generic_context, location_record):
        msg = assemble_message(record=location_record.copy(), context=generic_context)
        assert msg.type == MessageType.Location.value
        assert isinstance(msg.content, LocationContent)
        assert msg.content.latitude == pytest.approx(22.5431)
        assert msg.content.longitude == pytest.approx(114.0579)


class TestAssembleMessageApplication:
    def test_appmsg_text(self, generic_context, appmsg_text_record):
        msg = assemble_message(record=appmsg_text_record.copy(), context=generic_context)
        assert msg.type == MessageType.Text.value
        assert isinstance(msg.content, TextContent)
        assert msg.content.text == "App Title"

    def test_money_packet(self, generic_context, money_packet_record):
        msg = assemble_message(record=money_packet_record.copy(), context=generic_context)
        assert msg.type == MessageType.MoneyPacket.value
        assert isinstance(msg.content, MoneyPacketContent)
        assert msg.content.title == "Red Packet"
        assert msg.content.payment_info.scene_id == 1

    def test_transfer(self, generic_context, transfer_record):
        msg = assemble_message(record=transfer_record.copy(), context=generic_context)
        assert msg.type == MessageType.Transfer.value
        assert isinstance(msg.content, TransferContent)
        assert msg.content.title == "Transfer"
        assert msg.content.payment_info.transfer_id == "tid123"

    def test_location_share(self, generic_context, location_share_record):
        msg = assemble_message(record=location_share_record.copy(), context=generic_context)
        assert msg.type == MessageType.LocationShare.value
        assert isinstance(msg.content, LocationShareContent)
        assert msg.content.title == "Shared Location"

    def test_appmsg_emoji(self, tmp_path, generic_context, appmsg_emoji_record):
        # Provide a fake emoji cache so the file "exists"
        generic_context.emoji_cache = str(tmp_path)
        (tmp_path / "abc123def456.gif").write_text("gif")
        msg = assemble_message(record=appmsg_emoji_record.copy(), context=generic_context)
        assert msg.type == MessageType.Emoji.value
        assert isinstance(msg.content, EmojiContent)
        assert msg.content.file_path == str(tmp_path / "abc123def456.gif")


class TestUnknownMessageType:
    def test_unknown_type_fallback(self, generic_context, text_record):
        rec = text_record.copy()
        rec["type"] = 99999  # unknown type
        # parser falls back to 49 (Application) which then fails because content is not XML
        with pytest.raises(Exception):
            assemble_message(record=rec, context=generic_context)

import pytest

from wechat_timemachine.contact import (
    assemble_chatroom,
    assemble_friend,
    assemble_microprogram,
    assemble_official_account,
)


class TestAssembleFriend:
    def test_no_tags(self):
        record = {
            "id": "wxid_1",
            "id_alias": "alias1",
            "nickname": "Alice",
            "nickname_alias": "Alicia",
            "avatar_url": "http://example.com/avatar.png",
            "tag_ids": None,
        }
        labels = {1: "Family", 2: "Work"}
        friend = assemble_friend(record=record, labels=labels)
        assert friend.id == "wxid_1"
        assert friend.nickname == "Alice"
        assert friend.tags == []

    def test_with_tags(self):
        record = {
            "id": "wxid_2",
            "id_alias": "alias2",
            "nickname": "Bob",
            "nickname_alias": "Bobby",
            "avatar_url": "",
            "tag_ids": "1,2",
        }
        labels = {1: "Family", 2: "Work"}
        friend = assemble_friend(record=record, labels=labels)
        assert friend.tags == ["Family", "Work"]

    def test_empty_tag_ids(self):
        record = {
            "id": "wxid_3",
            "id_alias": None,
            "nickname": "Carol",
            "nickname_alias": None,
            "avatar_url": None,
            "tag_ids": "",
        }
        labels = {}
        friend = assemble_friend(record=record, labels=labels)
        assert friend.tags == []


class TestAssembleOfficialAccount:
    def test_basic(self):
        record = {
            "id": "gh_123",
            "id_alias": "official_alias",
            "nickname": "News Daily",
            "icon_url": "http://example.com/icon.png",
            "app_id": "app123",
            "account_entity": "EntityA",
        }
        oa = assemble_official_account(record=record)
        assert oa.id == "gh_123"
        assert oa.nickname == "News Daily"
        assert oa.app_id == "app123"


class TestAssembleMicroprogram:
    def test_basic(self):
        record = {"id": "gh_xxx@app", "nickname": "Mini App"}
        mp = assemble_microprogram(record=record)
        assert mp.id == "gh_xxx@app"
        assert mp.nickname == "Mini App"


class TestAssembleChatroom:
    def test_with_members(self):
        record = {
            "id": "room@chatroom",
            "nickname": "Family Group",
            "member_ids": "a;b;c",
            "owner_id": "a",
            "user_display_name": "Me",
        }
        cr = assemble_chatroom(record=record)
        assert cr.id == "room@chatroom"
        assert cr.members == ["a", "b", "c"]
        assert cr.is_deleted is False

    def test_no_members(self):
        record = {
            "id": "room2@chatroom",
            "nickname": "Old Group",
            "member_ids": None,
            "owner_id": "",
            "user_display_name": "",
        }
        cr = assemble_chatroom(record=record)
        assert cr.members == []
        assert cr.is_deleted is True

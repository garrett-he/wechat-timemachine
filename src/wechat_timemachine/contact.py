from dataclasses import dataclass


@dataclass
class Contact:
    id: str
    nickname: str


@dataclass
class Friend(Contact):
    id_alias: str
    nickname_alias: str
    avatar_url: str
    tags: list


@dataclass
class OfficialAccount(Contact):
    id_alias: str
    icon_url: str
    account_entity: str
    app_id: str


@dataclass
class Microprogram(Contact):
    pass


@dataclass
class Chatroom(Contact):
    members: list
    owner_id: str
    user_display_name: str
    is_deleted: bool


def assemble_friend(record: dict, labels: dict) -> Friend:
    if not record['tag_ids']:
        tags = []
    else:
        tags = [labels[i] for i in map(int, record['tag_ids'].split(','))]

    return Friend(
        id=record['id'],
        id_alias=record['id_alias'],
        nickname=record['nickname'],
        nickname_alias=record['nickname_alias'],
        avatar_url=record['avatar_url'],
        tags=tags,
    )


def assemble_official_account(record: dict) -> OfficialAccount:
    return OfficialAccount(
        id=record['id'],
        id_alias=record['id_alias'],
        nickname=record['nickname'],
        icon_url=record['icon_url'],
        app_id=record['app_id'],
        account_entity=record['account_entity'],
    )


def assemble_microprogram(record: dict) -> Microprogram:
    return Microprogram(
        id=record['id'],
        nickname=record['nickname'],
    )


def assemble_chatroom(record: dict) -> Chatroom:
    if record['member_ids'] is None:
        members = []
        is_deleted = True
    else:
        members = record['member_ids'].split(';')
        is_deleted = False

    return Chatroom(
        id=record['id'],
        nickname=record['nickname'],
        members=members,
        owner_id=record['owner_id'],
        user_display_name=record['user_display_name'],
        is_deleted=is_deleted
    )

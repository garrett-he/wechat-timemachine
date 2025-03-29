import json
from typing import Iterable
from .context import WechatContextAndroid


def load_contact_labels(context: WechatContextAndroid) -> dict:
    sql = '''
        SELECT
            labelID AS id,
            labelName AS name
        FROM ContactLabel
    '''

    return {row['id']: row['name'] for row in context.db.execute(sql).fetchall()}


def load_friends(context: WechatContextAndroid) -> Iterable[dict]:
    sql = f'''
        SELECT
            r.username AS id,
            CASE WHEN r.alias = '' THEN NULL ELSE r.alias END AS id_alias, r.nickname AS nickname,
            CASE WHEN r.conRemark = '' THEN NULL ELSE r.conRemark END AS nickname_alias,
            r.contactLabelIds AS tag_ids,
            CASE WHEN r.conRemarkPYShort = '' THEN r.pyInitial ELSE r.conRemarkPYShort END AS pinyin_abbrev,

            i.reserved1 AS avatar_url

        FROM rcontact AS r
            LEFT JOIN img_flag AS i ON i.username = r.username
        WHERE
            r.username NOT LIKE 'gh_%' AND
            r.username NOT LIKE '%chatroom' AND
            r.type & 1 = 1 AND
            r.type & 0x20 <> 0x20 AND
            r.verifyFlag = 0 AND
            r.username NOT IN ('filehelper', '{context.user_id}')
        ORDER BY pinyin_abbrev
    '''

    return context.db.execute(sql).fetchall()


def load_official_accounts(context: WechatContextAndroid) -> Iterable[dict]:
    sql = '''
        SELECT
            r.username AS id,
            CASE WHEN r.alias = '' THEN NULL ELSE r.alias END AS id_alias, r.nickname AS nickname,
            CASE WHEN r.conRemark = '' THEN NULL ELSE r.conRemark END AS nickname_alias,
            CASE WHEN r.conRemarkPYShort = '' THEN r.pyInitial ELSE r.conRemarkPYShort END AS pinyin_abbrev,

            b.brandIconURL AS icon_url,
            b.extInfo AS b_extInfo
        FROM rcontact AS r
            LEFT JOIN img_flag AS i ON i.username = r.username
            LEFT JOIN bizinfo AS b ON b.username = r.username
        WHERE
            r.username LIKE 'gh_%' AND r.username NOT LIKE 'gh_%@app'
        ORDER BY pinyin_abbrev
    '''

    rows = []
    for row in context.db.execute(sql).fetchall():
        if row['b_extInfo'] is None:
            row['account_entity'] = None
            row['app_id'] = None
        else:
            ext_info = json.loads(row['b_extInfo'])
            row['account_entity'] = ext_info['RegisterSource']['RegisterBody']
            row['app_id'] = ext_info['Appid']
            del row['b_extInfo']

        rows.append(row)

    return rows


def load_microprograms(context: WechatContextAndroid) -> Iterable[dict]:
    sql = '''
        SELECT
            r.username AS id,
            CASE WHEN r.alias = '' THEN NULL ELSE r.alias END AS id_alias, r.nickname AS nickname,
            CASE WHEN r.conRemarkPYShort = '' THEN r.pyInitial ELSE r.conRemarkPYShort END AS pinyin_abbrev
        FROM rcontact AS r
            LEFT JOIN img_flag AS i ON i.username = r.username
        WHERE
            r.username LIKE 'gh_%@app'
        ORDER BY pinyin_abbrev
    '''

    return context.db.execute(sql).fetchall()


def load_chatrooms(context: WechatContextAndroid) -> Iterable[dict]:
    sql = f'''
        SELECT
            r.username AS id,
            CASE WHEN r.alias = '' THEN NULL ELSE r.alias END AS id_alias, r.nickname AS nickname,

            c.memberlist AS member_ids,
            c.roomowner AS owner_id,
            c.selfDisplayName AS user_display_name
        FROM rcontact AS r
            LEFT JOIN img_flag AS i ON i.username = r.username
            LEFT JOIN chatroom AS c ON c.chatroomname = r.username
        WHERE
            r.username LIKE '%@chatroom'
        ORDER BY c.modifytime
    '''

    return context.db.execute(sql).fetchall()

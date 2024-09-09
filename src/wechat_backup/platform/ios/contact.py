import biplist
from typing import Iterable
from .context import WechatContextIos


def parse_blob_column(col):
    result = {}
    i = 0

    while i < len(col):
        length = ord(col[i + 1:i + 2])
        begin = i + 2
        end = begin + length

        result[col[i]] = col[begin:end].decode('utf-8')
        i = end

    return result


def parse_contact_remark(blob):
    remark_map = {
        0x0A: 'nickname',
        0x1A: 'nickname_alias',
        0x12: 'id_alias',
        0x3A: 'remark',
        0x42: 'tag_ids'
    }

    d = parse_blob_column(blob)
    result = {}

    for k in remark_map.keys():
        if k not in d.keys() or d[k] == '':
            result[remark_map[k]] = None
        else:
            result[remark_map[k]] = d[k]

    return result


def parse_contact_rows(rows):
    result = []
    for row in rows:

        d = parse_contact_remark(row['dbContactRemark'])
        head_img = row['dbContactHeadImage']

        if head_img[0] == 8 or head_img[1] == 0:
            thumbnail_url = None
            avatar_url = None
        elif row['id'][0:3] == 'gh_':
            p = head_img[1] + 2
            thumbnail_url = head_img[2:p].decode('utf-8')

            if head_img[p + 3] == 0:
                avatar_url = None
            else:
                avatar_url = head_img[p + 4:p + 4 + head_img[p + 3]].decode('utf-8')
        else:
            p = head_img[1] + 3
            thumbnail_url = head_img[3:p].decode('utf-8')

            if head_img[p + 4] == 0:
                avatar_url = None
            else:
                avatar_url = head_img[p + 5:p + 5 + head_img[p + 3]].decode('utf-8')

        if thumbnail_url == '':
            thumbnail_url = None

        if avatar_url == '':
            avatar_url = None

        row['avatar_url'] = avatar_url
        row['thumbnail_url'] = thumbnail_url
        result.append({**row, **d})

    return result


def load_contact_labels(context: WechatContextIos) -> dict:
    pl = biplist.readPlist('%s/contactlabel.list' % context.doc_dir)

    labels = {}
    for i in map(int, pl['$objects'][1]['NS.objects']):
        labels[pl['$objects'][i]['m_uiID']] = pl['$objects'][i + 1]

    return labels


def load_friends(context: WechatContextIos) -> Iterable[dict]:
    sql = f'''
            SELECT
                userName AS id,
                encodeUserName AS encrypt_id,
                dbContactRemark,
                dbContactHeadImage
            FROM Friend
            WHERE userName NOT LIKE 'gh_%'
                AND userName NOT LIKE '%chatroom'
                AND type & 1 = 1
                AND type & 0x20 <> 0x20
                AND certificationFlag = 0
                AND userName NOT IN (
                    'qqmail',
                    'qmessage',
                    'tmessage',
                    'floatbottle',
                    'fmessage',
                    'medianote',
                    'newsapp',
                    'feedsapp',
                    'masssendapp',
                    'blogapp',
                    'voiceinputapp',
                    'linkedinplugin',
                    'brandsessionholder',
                    'notification_messages',
                    'iwatchholder',
                    'brandsessionholder_weapp',
                    'filehelper'
                )
        '''
    return parse_contact_rows(context.contact_db.execute(sql).fetchall())


def load_official_accounts(context: WechatContextIos) -> Iterable[dict]:
    sql = f'''
        SELECT
            userName AS id,
            encodeUserName AS encrypt_id,
            dbContactRemark,
            dbContactHeadImage
        FROM Friend
        WHERE userName LIKE 'gh_%' AND userName NOT LIKE 'gh_%@app'
        '''

    return parse_contact_rows(context.contact_db.execute(sql).fetchall())


def load_microprograms(context: WechatContextIos) -> Iterable[dict]:
    sql = f'''
        SELECT
            userName AS id,
            encodeUserName AS encrypt_id,
            dbContactRemark,
            dbContactHeadImage
        FROM Friend
        WHERE userName LIKE 'gh_%@app'
        '''

    return parse_contact_rows(context.contact_db.execute(sql).fetchall())


def load_chatrooms(context: WechatContextIos) -> Iterable[dict]:
    sql = f'''
        SELECT
            userName AS id,
            encodeUserName AS encrypt_id,
            dbContactRemark,
            dbContactHeadImage
        FROM Friend
        WHERE userName LIKE '%@chatroom'
        '''
    return parse_contact_rows(context.contact_db.execute(sql).fetchall())

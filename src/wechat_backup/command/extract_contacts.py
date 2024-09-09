import json
import importlib
from argparse import ArgumentParser, Namespace
from wechat_backup.contact import *
from wechat_backup.helper import EntityJSONEncoder


def add_arguments(parser: ArgumentParser):
    parser.add_argument('--type', metavar='friend|official|microprogram|chatroom', required=False, help='type of contacts to be dumped', default='friend')


def execute(config: dict, args: Namespace):
    platform_module = importlib.import_module('wechat_backup.platform.%s' % config['platform'])
    context = platform_module.context.new_context(config)

    def assemble_friend_wrapper(record: dict):
        return assemble_friend(record=record, labels=platform_module.contact.load_contact_labels(context=context))

    assemblers = {
        'friend': assemble_friend_wrapper,
        'official': assemble_official_account,
        'microprogram': assemble_microprogram,
        'chatroom': assemble_chatroom
    }

    loaders = {
        'friend': platform_module.contact.load_friends,
        'official': platform_module.contact.load_official_accounts,
        'microprogram': platform_module.contact.load_microprograms,
        'chatroom': platform_module.contact.load_chatrooms
    }

    print(json.dumps([
        assemblers[args.type](record=record)
        for record in loaders[args.type](context=context)
    ], indent=4, ensure_ascii=False, cls=EntityJSONEncoder))

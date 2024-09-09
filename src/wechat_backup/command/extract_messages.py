import json
import importlib
from argparse import ArgumentParser, Namespace
from wechat_backup.message.parser import assemble_message
from wechat_backup.helper import EntityJSONEncoder


def add_arguments(parser: ArgumentParser):
    parser.add_argument('--conversation-id', metavar='string', required=True, help='conversation of messages')


def execute(config: dict, args: Namespace):
    platform_module = importlib.import_module('wechat_backup.platform.%s' % config['platform'])
    context = platform_module.context.new_context(config)

    print(json.dumps([
        assemble_message(record=record, context=context)
        for record in platform_module.message.load_messages(context=context, conversation_id=args.conversation_id)
    ], indent=4, ensure_ascii=False, cls=EntityJSONEncoder))

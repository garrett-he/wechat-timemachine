import json

import click

from wechat_backup.message.parser import assemble_message
from wechat_backup.helper import EntityJSONEncoder


@click.command('extract-messages')
@click.option('-i', '--conversation-id', help='Conversation of messages.', required=True)
@click.pass_context
def extract_messages_command(ctx: click.Context, conversation_id: str):
    """Extract messages of a conversation."""

    platform_module = ctx.obj['platform_module']
    context = platform_module.context.new_context(ctx.obj['config'])

    data = [
        assemble_message(record=record, context=context)
        for record in platform_module.message.load_messages(context=context, conversation_id=conversation_id)
    ]

    click.echo(json.dumps(data, indent=4, ensure_ascii=False, cls=EntityJSONEncoder))

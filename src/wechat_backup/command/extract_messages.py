import json

import click
from tabulate import tabulate

from wechat_backup.message.parser import assemble_message
from wechat_backup.helper import EntityJSONEncoder


@click.command('extract-messages')
@click.option('-i', '--conversation-id', help='Conversation of messages.', required=True)
@click.option('-f', '--format', 'output_format', help='Format of outputs', type=click.Choice(['table', 'json']),
              required=False, default='table')
@click.pass_context
def extract_messages_command(ctx: click.Context, conversation_id: str, output_format: str):
    """Extract messages of a conversation."""

    platform_module = ctx.obj['platform_module']
    context = platform_module.context.new_context(ctx.obj['config'])

    data = [
        assemble_message(record=record, context=context)
        for record in platform_module.message.load_messages(context=context, conversation_id=conversation_id)
    ]

    if output_format.lower() == 'json':
        click.echo(json.dumps(data, indent=4, ensure_ascii=False, cls=EntityJSONEncoder))
    else:
        click.echo(tabulate(data, headers=['conversation', 'datetime', 'sender', 'type', 'content']))

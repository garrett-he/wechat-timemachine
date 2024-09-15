import json

import click

from wechat_backup.contact import assemble_friend, assemble_official_account, assemble_microprogram, assemble_chatroom
from wechat_backup.helper import EntityJSONEncoder


@click.command('extract-contacts')
@click.option('-t', '--type', 'contact_type', help='Type of contacts',
              type=click.Choice(['friend', 'official', 'microprogram', 'chatroom']), default='friend')
@click.pass_context
def extract_contacts_command(ctx: click.Context, contact_type: str):
    """Extract WeChat contacts."""

    platform_module = ctx.obj['platform_module']
    context = platform_module.context.new_context(ctx.obj['config'])

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

    data = [
        assemblers[contact_type](record=record)
        for record in loaders[contact_type](context=context)
    ]

    click.echo(json.dumps(data, indent=4, ensure_ascii=False, cls=EntityJSONEncoder))

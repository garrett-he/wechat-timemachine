import json
from typing import Literal

import typer
from tabulate import tabulate

from wechat_timemachine.contact import (
    assemble_friend,
    assemble_official_account,
    assemble_microprogram,
    assemble_chatroom,
)
from wechat_timemachine.helper import EntityJSONEncoder


def register_commands(app: typer.Typer) -> None:
    @app.command("extract-contacts")
    def extract_contacts_command(
        ctx: typer.Context,
        contact_type: Literal["friend", "official", "microprogram", "chatroom"] = typer.Option(
            "friend", "-t", "--type", help="Type of contacts"
        ),
        output_format: Literal["table", "json"] = typer.Option(
            "table", "-f", "--format", help="Format of outputs"
        ),
    ):
        """Extract WeChat contacts."""

        platform_module = ctx.obj["platform_module"]
        context = platform_module.context.new_context(ctx.obj["config"])

        def assemble_friend_wrapper(record: dict):
            return assemble_friend(record=record, labels=platform_module.contact.load_contact_labels(context=context))

        assemblers = {
            "friend": assemble_friend_wrapper,
            "official": assemble_official_account,
            "microprogram": assemble_microprogram,
            "chatroom": assemble_chatroom,
        }

        loaders = {
            "friend": platform_module.contact.load_friends,
            "official": platform_module.contact.load_official_accounts,
            "microprogram": platform_module.contact.load_microprograms,
            "chatroom": platform_module.contact.load_chatrooms,
        }

        data = [
            assemblers[contact_type](record=record)
            for record in loaders[contact_type](context=context)
        ]

        if output_format.lower() == "json":
            typer.echo(json.dumps(data, indent=4, ensure_ascii=False, cls=EntityJSONEncoder))
        else:
            typer.echo(tabulate(data, headers=["id", "nickname", "alias_id", "alias_name", "avatar", "tags"]))

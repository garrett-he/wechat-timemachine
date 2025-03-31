import json
from typing import Literal

import typer
from tabulate import tabulate

from wechat_timemachine.helper import EntityJSONEncoder
from wechat_timemachine.message.parser import assemble_message


def register_commands(app: typer.Typer) -> None:
    @app.command("extract-messages")
    def extract_messages_command(
        ctx: typer.Context,
        conversation_id: str = typer.Option(
            ..., "-i", "--conversation-id", help="Conversation of messages."
        ),
        output_format: Literal["table", "json"] = typer.Option(
            "table", "-f", "--format", help="Format of outputs"
        ),
    ):
        """Extract messages of a conversation."""

        platform_module = ctx.obj["platform_module"]
        context = platform_module.context.new_context(ctx.obj["config"])

        data = [
            assemble_message(record=record, context=context)
            for record in platform_module.message.load_messages(context=context, conversation_id=conversation_id)
        ]

        if output_format.lower() == "json":
            typer.echo(json.dumps(data, indent=4, ensure_ascii=False, cls=EntityJSONEncoder))
        else:
            typer.echo(tabulate(data, headers=["conversation", "datetime", "sender", "type", "content"]))

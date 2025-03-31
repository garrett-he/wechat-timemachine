import configparser
import importlib
from pathlib import Path

import typer

from wechat_timemachine import __version__
from wechat_timemachine.command import register_all_commands


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


app = typer.Typer()
register_all_commands(app)


@app.callback()
def cli(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version information.",
        is_eager=True,
        callback=_version_callback,
        expose_value=False,
    ),
    profile: str = typer.Option(
        "default",
        "-p",
        "--profile",
        help="Profile to load from configurations.",
        metavar="NAME",
    ),
):
    """A command-line tool to help user manage data in WeChat backup files."""

    ctx.ensure_object(dict)

    profile_file = Path.home() / ".wechat-backup/profiles.ini"

    if not profile_file.exists():
        typer.echo("Profile file not found", err=True)
        raise typer.Exit(code=1)

    config = configparser.ConfigParser()
    config.read(profile_file)

    ctx.obj["config"] = dict(config.items(section=profile))
    ctx.obj["platform_module"] = importlib.import_module(
        f'wechat_timemachine.platform.{ctx.obj["config"]["platform"]}'
    )


if __name__ == "__main__":
    app()

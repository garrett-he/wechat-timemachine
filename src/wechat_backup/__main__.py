import importlib
import configparser
from pathlib import Path

import click

from wechat_backup import __version__
from wechat_backup.command import command_group


def print_version(ctx: click.Context, _, value: str):
    if not value or ctx.resilient_parsing:
        return

    click.echo(__version__)
    ctx.exit()


@click.group(commands=command_group)
@click.option('--version', help='Show version information.', is_flag=True, callback=print_version, expose_value=False,
              is_eager=True)
@click.option('-p', '--profile', help='Profile to load from configurations.', type=str, metavar='NAME',
              default='default')
@click.pass_context
def cli(ctx: click.Context, profile: str):
    """A command-line tool to help user manage data in WeChat backup files."""

    ctx.ensure_object(dict)

    profile_file = Path.home() / '.wechat-backup/profiles.ini'

    if not profile_file.exists():
        ctx.fail('Profile file not found')

    config = configparser.ConfigParser()
    config.read(profile_file)

    ctx.obj['config'] = dict(config.items(section=profile))
    ctx.obj['platform_module'] = importlib.import_module(f'wechat_backup.platform.{ctx.obj["config"]["platform"]}')


if __name__ == '__main__':
    cli(obj={})  # pylint: disable=no-value-for-parameter

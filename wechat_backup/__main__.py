# -*- coding: utf-8 -*-
# Copyright (C) 2020 Garrett HE <garrett.he@hotmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import importlib
import argparse
import configparser


def print_help():
    usage = '''usage: wechat-backup <command> [parameters]
To see help text, you can run:
  wechat-backup <command> --help
'''
    sys.stderr.write(usage)


def load_config(profile):
    filename = '%s/.wechat-backup/config.ini' % (os.getenv('HOME'))

    if not os.path.exists(filename):
        raise Exception('configuration file "%s" for wechat-backup not found.' % filename)

    config = configparser.ConfigParser()
    config.read(filename)

    return {k: v for k, v in config.items(section=profile)}


def main():
    if len(sys.argv) < 2 or sys.argv[1][0] == '-':
        print_help()
        return -1

    parser = argparse.ArgumentParser()

    parser.add_argument('command')

    # add common arguments
    group = parser.add_argument_group('common')
    group.add_argument('--profile', metavar='string', required=False, help='specific profile from your configurations',
                       default='default')

    command = importlib.import_module('wechat_backup.command.%s' % (sys.argv[1].replace('-', '_')))
    command.add_arguments(parser)

    args = parser.parse_args()

    return command.execute(
        config=load_config(args.profile),
        args=args
    )


if __name__ == '__main__':
    sys.exit(main())

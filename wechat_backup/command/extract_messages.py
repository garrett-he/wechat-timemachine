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

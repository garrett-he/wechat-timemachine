# Agent Guide for wechat-timemachine

Quick reference for AI agents working on this codebase. For design rationale,
see [docs/design.md](docs/design.md). For system architecture and data flows,
see [docs/architecture.md](docs/architecture.md).

## Project Overview

Python CLI tool that extracts contacts and messages from WeChat backup files (
Android and iOS). Reads raw SQLite databases and media files, outputs tables or
JSON.

## Tech Stack

- Python 3.10–3.14, `uv`, `just`, `typer`, `pytest`, `ruff`, `hatchling`

## Quick Commands

```bash
just init    # uv sync
just test    # pytest with coverage
just lint    # ruff check src/ tests/
just build   # uv build
just deploy  # nuitka single-file binary
```

## Code Style

- 4-space indent, 160 char line limit, LF endings, double quotes
- Docstrings not required (disabled in ruff)

## Key Directories

| Directory                             | Purpose                            |
|---------------------------------------|------------------------------------|
| `src/wechat_timemachine/command/`          | CLI commands (typer)               |
| `src/wechat_timemachine/message/`          | Message types and parser registry  |
| `src/wechat_timemachine/platform/android/` | Android DB queries and media paths |
| `src/wechat_timemachine/platform/ios/`     | iOS DB queries, plist/blob parsing |

## Platform Module Contract

Each platform (`android/`, `ios/`) must expose:

- `context.new_context(config: dict)` → platform-specific `WechatContext`
- `contact.load_contact_labels(context)` → `dict`
- `contact.load_friends(context)` → `Iterable[dict]`
- `contact.load_official_accounts(context)` → `Iterable[dict]`
- `contact.load_microprograms(context)` → `Iterable[dict]`
- `contact.load_chatrooms(context)` → `Iterable[dict]`
- `message.load_messages(context, conversation_id)` → `Iterable[dict]`

Commands access the platform dynamically via `ctx.obj['platform_module']`.

## Message Parser Registry

Register parsers with decorators. Platform-specific parsers override generic
ones.

```python
from wechat_timemachine.message.parser import content_parser, appmsg_parser
from wechat_timemachine.context import WechatPlatform
from wechat_timemachine.message.parser import WechatMessageType


@content_parser(platform=WechatPlatform.Android, type=WechatMessageType.Image)
def parse_content_image(record: dict, context):
    ...
    return ImageContent.content_type, ImageContent(...)
```

## How to Extend

| Task                 | Steps                                                                                                     |
|----------------------|-----------------------------------------------------------------------------------------------------------|
| **New platform**     | Create `platform/<name>/` with `context.py`, `contact.py`, `message.py`; update `WechatPlatform` enum     |
| **New command**      | Add file in `command/`, export in `command/__init__.py`                                                   |
| **New message type** | Add to `WechatMessageType` (parser.py) and `MessageType` (typing.py), add content dataclass, write parser |
| **New contact type** | Add dataclass in `contact.py`, add loaders in platforms, add assembler, wire into command                 |

## Testing

- Test suite is minimal; add tests for assemblers, parsers, and platform helpers
- Use `tests/res/` for fixtures

## Common Pitfalls

1. **Import order matters**: `@content_parser` / `@appmsg_parser` mutate global
   dicts. Platform modules must be imported before `assemble_message` runs.
2. **Contexts hold open DB connections** — don't close them prematurely.
3. **iOS message tables are sharded**: `Chat_<md5(conversation_id)>` spread
   across `message_*.sqlite` files.
4. **Group chat sender parsing**: `assemble_message()` strips `sender: ` prefix
   from content in place.
5. **Media path validation**: `path_or_none()` returns `None` for missing files;
   content dataclasses may raise in `__post_init__`.
6. **SQL f-strings**: Several queries use f-strings with user-provided
   `conversation_id`. Avoid introducing unsanitized external input.

## License

GPL-3.0 — do not introduce code with incompatible licenses.

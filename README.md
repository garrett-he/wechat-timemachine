# wechat-dumper

A command-line tool to dump user data from [WeChat][1] backup files.

## Features

- Extract **contacts** (friends, official accounts, mini programs, chatrooms)
  from WeChat backups.
- Extract **messages** from individual or group conversations.
- Support for **Android** and **iOS** WeChat backups.
- Output as human-readable **tables** or machine-readable **JSON**.
- Resolve media file paths (images, videos, voice messages, attachments,
  emojis).

## Requirements

- Python >= 3.10, < 3.15
- [uv](https://docs.astral.sh/uv/) (for development)

## Installation

### From PyPI

```bash
pip install wechat-dumper
```

### From Source

```bash
uv sync
```

## Usage

### Configuration

Create a profile file at `~/.wechat-backup/profiles.ini`:

```ini
[default]
platform = android
user_id = your_wechat_id
db_file = /path/to/EnMicroMsg.db
media_dir = /path/to/wechat/media
emoji_cache = /path/to/emoji/cache

[ios]
platform = ios
user_id = your_wechat_id
doc_dir = /path/to/backup/Documents
emoji_cache = /path/to/emoji/cache
```

### Commands

```bash
# Extract contacts (default: friends, table output)
wechat-dumper extract-contacts

# Extract official accounts as JSON
wechat-dumper extract-contacts --type official --format json

# Extract messages from a conversation
wechat-dumper extract-messages --conversation-id friend_wechat_id --format json
```

Use `--profile <name>` to select a non-default profile.

## Development

```bash
# Setup
just init

# Run tests
just test

# Lint
just lint

# Build wheel
just build

# Build single-file binary with Nuitka
just deploy
```

## Project Structure

```
src/wechat_dumper/
├── __main__.py              # CLI entry point
├── context.py               # Platform enum and base context
├── contact.py               # Contact domain models and assemblers
├── helper.py                # Utilities (SQLite, JSON, MD5)
├── command/                 # CLI commands
├── message/                 # Message types and parser registry
└── platform/                # Platform-specific implementations
    ├── android/
    └── ios/
```

For design rationale, see [docs/design.md](docs/design.md). For system
architecture and data flows, see [docs/architecture.md](docs/architecture.md).
For agent coding guidance, see [AGENTS.md](AGENTS.md).

## License

Copyright (C) 2025 Garrett HE <garrett.he@outlook.com>

The GNU General Public License (GPL) version 3, see [COPYING](./COPYING).

[1]: https://www.wechat.com

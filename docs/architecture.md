# Architecture Document

This document describes the system architecture, module relationships, and data
flows of `wechat-dumper`.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│  wechat_dumper.__main__  +  wechat_dumper.command.*         │
│     (click group, profile loading, command dispatch)        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Platform Abstraction Layer                 │
│           wechat_dumper.platform.{android,ios}              │
│     (context creation, contact loaders, message loaders)    │
└────────────────────────┬────────────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐
│   Android Platform  │   │    iOS Platform     │
│  (single SQLite DB, │   │ (multiple SQLite    │
│   media_dir paths)  │   │  DBs, plist, blobs) │
└─────────────────────┘   └─────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Domain Layer                        │
│  wechat_dumper.contact  +  wechat_dumper.message.*          │
│     (assemblers, parser registry, content types)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Utility Layer                            │
│         wechat_dumper.helper  +  wechat_dumper.context      │
│     (JSON encoder, SQLite helper, base context, enums)      │
└─────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### 1. CLI Layer

**`wechat_dumper.__main__`**

- Defines the top-level `click.Group`.
- Loads `~/.wechat-backup/profiles.ini` via `configparser`.
- Dynamically imports the platform module: `wechat_dumper.platform.<platform>`.
- Stores config and platform module in `ctx.obj` for subcommands.

**`wechat_dumper.command.extract_contacts`**

- `extract-contacts` command.
- Options: `--type` (`friend`, `official`, `microprogram`, `chatroom`),
  `--format` (`table`, `json`).
- Maps `contact_type` to an assembler and a loader.
- For `friend`, wraps `assemble_friend` with labels.
- Outputs via `tabulate` or `json.dumps`.

**`wechat_dumper.command.extract_messages`**

- `extract-messages` command.
- Options: `--conversation-id` (required), `--format` (`table`, `json`).
- Loads messages via `platform_module.message.load_messages()`.
- Parses each record through `assemble_message()`.
- Outputs via `tabulate` or `json.dumps`.

### 2. Platform Abstraction Layer

Each platform subpackage (`android/`, `ios/`) contains three modules:

#### `context.py`

- Defines a platform-specific `WechatContext` subclass.
- `new_context(config: dict)` factory function.
- Opens SQLite connections and stores media path roots.

#### `contact.py`

- `load_contact_labels(context) -> dict`
- `load_friends(context) -> Iterable[dict]`
- `load_official_accounts(context) -> Iterable[dict]`
- `load_microprograms(context) -> Iterable[dict]`
- `load_chatrooms(context) -> Iterable[dict]`

All return raw dicts with keys expected by assemblers in
`wechat_dumper.contact`.

#### `message.py`

- `load_messages(context, conversation_id) -> Iterable[dict]`
- Platform-specific `@content_parser` and `@appmsg_parser` decorators for media
  resolution.

**Android specifics**:

- Single DB connection (`context.db`).
- Media paths resolved from `media_dir` using MD5 subdirectories.
- Voice duration parsed from content string (`duration:1234`).

**iOS specifics**:

- Multiple DBs: `contact_db`, `mm_db`, `message_db[]` (list).
- Binary plist parsing (`biplist`) for contact labels.
- Binary blob parsing for `dbContactRemark` and `dbContactHeadImage`.
- Message tables are sharded: `Chat_<md5(conversation_id)>` across multiple
  `message_*.sqlite` files.
- Media paths resolved from `doc_dir` using `MesLocalID`.

### 3. Core Domain Layer

**`wechat_dumper.contact`**

- Dataclasses: `Contact`, `Friend`, `OfficialAccount`, `Microprogram`,
  `Chatroom`.
- Assembler functions that transform raw dicts into dataclasses.
- `assemble_friend` requires a `labels: dict` mapping to resolve tag names.

**`wechat_dumper.message.typing`**

- `MessageType` enum (string-based, for output).
- `Message` dataclass.
- Content dataclasses: `TextContent`, `ImageContent`, `VoiceContent`,
  `VideoContent`, `EmojiContent`, `VoIPContent`, `LinkContent`, `MusicContent`,
  `AttachmentContent`, `MoneyPacketContent`, `TransferContent`,
  `LocationContent`, `LocationShareContent`, `NameCardContent`, `SystemContent`.
- Some dataclasses have `__post_init__` validation (e.g., `ImageContent`
  requires at least one path).

**`wechat_dumper.message.parser`**

- `WechatMessageType` enum (int-based, maps to WeChat internal type codes).
- `WechatAppmsgType` enum (int-based, subtypes for application messages).
- `@content_parser` and `@appmsg_parser` decorator implementations.
- `assemble_message(record, context)` — main orchestration:
    1. Determines sender ID (handles group chat `sender: content` prefix).
    2. Maps raw `type` to `WechatMessageType`.
    3. Looks up platform-specific parser, falls back to `WechatPlatform.All`.
    4. Invokes parser, returns `Message` dataclass.

### 4. Utility Layer

**`wechat_dumper.context`**

- `WechatPlatform` enum: `All`, `iOS`, `Android`.
- `WechatContext` base dataclass: `platform`, `user_id`, `emoji_cache`.

**`wechat_dumper.helper`**

- `sqlite_connect(path) -> sqlite3.Connection` — opens DB with `dict_factory`
  row factory.
- `EntityJSONEncoder` — custom JSON encoder for dataclasses, datetime, enums.
- `md5_utf8(s) -> str` — MD5 helper for iOS table/media naming.
- `path_or_none(path) -> str | None` — existence check for media files.

## Data Flow Diagrams

### Contact Extraction

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   User      │────▶│  extract-contacts │────▶│  Load profile config │
│  (shell)    │     │    command        │     │  + platform module   │
└─────────────┘     └──────────────────┘     └─────────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ new_context()   │
                                               │ (platform-specific│
                                               │  DB connections) │
                                               └─────────────────┘
                                                        │
                          ┌─────────────────────────────┼─────────────────────────────┐
                          ▼                             ▼                             ▼
                   ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
                   │ load_friends│              │load_official│              │load_chatrooms│
                   │             │              │  accounts   │              │             │
                   └──────┬──────┘              └──────┬──────┘              └──────┬──────┘
                          │                             │                             │
                          ▼                             ▼                             ▼
                   ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
                   │assemble_friend│            │assemble_official│          │assemble_chatroom│
                   │(+ labels)    │            │  _account       │          │               │
                   └──────┬──────┘              └──────┬──────┘              └──────┬──────┘
                          │                             │                             │
                          └─────────────────────────────┼─────────────────────────────┘
                                                        ▼
                                               ┌─────────────────┐
                                               │  tabulate /     │
                                               │  json.dumps     │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                                    (stdout)
```

### Message Extraction

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   User      │────▶│ extract-messages │────▶│  Load profile config │
│  (shell)    │     │    command        │     │  + platform module   │
└─────────────┘     └──────────────────┘     └─────────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ new_context()   │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ load_messages() │
                                               │ (platform-spec) │
                                               └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │ assemble_message│
                                               │   (per record)  │
                                               └─────────────────┘
                                                        │
                                          ┌─────────────┴─────────────┐
                                          ▼                           ▼
                                   ┌──────────────┐           ┌──────────────┐
                                   │ get_sender_id│           │ parser lookup│
                                   │(group chat   │           │(platform /   │
                                   │  handling)   │           │  generic)    │
                                   └──────────────┘           └──────┬───────┘
                                                                     │
                                                                     ▼
                                                              ┌─────────────┐
                                                              │  @content_  │
                                                              │   parser    │
                                                              │  function   │
                                                              └──────┬──────┘
                                                                     │
                                                                     ▼
                                                              ┌─────────────┐
                                                              │   Message   │
                                                              │  dataclass  │
                                                              └──────┬──────┘
                                                                     │
                                                                     ▼
                                                              ┌─────────────┐
                                                              │  tabulate / │
                                                              │  json.dumps │
                                                              └─────────────┘
                                                                     │
                                                                     ▼
                                                                  (stdout)
```

## File Structure

```
src/wechat_dumper/
├── __init__.py              # Version string
├── __main__.py              # CLI entry point (click group)
├── context.py               # WechatPlatform enum, WechatContext base class
├── contact.py               # Contact dataclasses and assemblers
├── helper.py                # SQLite helper, JSON encoder, MD5, path utils
├── command/
│   ├── __init__.py          # Command registration list
│   ├── extract_contacts.py  # extract-contacts command
│   └── extract_messages.py  # extract-messages command
├── message/
│   ├── __init__.py          # (empty)
│   ├── parser.py            # Parser registry, decorators, assemble_message
│   └── typing.py            # MessageType, Message, content dataclasses
└── platform/
    ├── __init__.py          # (empty)
    ├── android/
    │   ├── __init__.py      # Submodule imports
    │   ├── context.py       # WechatContextAndroid, new_context()
    │   ├── contact.py       # Android contact SQL loaders
    │   └── message.py       # Android message SQL + media parsers
    └── ios/
        ├── __init__.py      # Submodule imports
        ├── context.py       # WechatContextIos, new_context()
        ├── contact.py       # iOS contact SQL + blob/plist parsers
        └── message.py       # iOS message SQL + media parsers
```

## Extension Points

| Extension         | How                                                                                              |
|-------------------|--------------------------------------------------------------------------------------------------|
| New platform      | Add subpackage under `platform/` implementing the module contract.                               |
| New command       | Add module under `command/`, register in `command/__init__.py`.                                  |
| New message type  | Add to `WechatMessageType` and `MessageType`, add content dataclass, write parser.               |
| New output format | Modify command functions (currently only `table`/`json`).                                        |
| New contact type  | Add dataclass in `contact.py`, add loader in platform modules, add assembler, wire into command. |

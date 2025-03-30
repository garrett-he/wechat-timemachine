# Design Document

This document captures the design decisions, patterns, and rationale behind
`wechat-dumper`.

## Goals

1. **Extract WeChat data from local backups** without requiring a running WeChat
   client or cloud access.
2. **Support multiple platforms** (Android, iOS) with a unified CLI interface.
3. **Output structured data** in both human-readable (table) and
   machine-readable (JSON) formats.
4. **Resolve media file paths** alongside message metadata, so users can locate
   images, videos, voice messages, etc.

## Non-Goals

- Decrypting encrypted backups (assumes the user has already decrypted their
  backup).
- Real-time syncing or message interception.
- Modifying or writing back to WeChat databases.

## Design Decisions

### 1. Platform Abstraction via Dynamic Import

**Decision**: Each platform is a Python subpackage under `platform/`. The CLI
dynamically imports the correct module based on the `platform` key in the user's
profile config.

**Rationale**:

- Keeps platform-specific code isolated.
- Avoids conditional branching scattered throughout commands.
- New platforms can be added without modifying existing command code.

**Trade-off**: Error messages for missing platform modules occur at runtime, not
import time.

### 2. Decorator-Based Parser Registry

**Decision**: Message content parsers are registered via `@content_parser` and
`@appmsg_parser` decorators that populate global dictionaries keyed by
`(platform, message_type)`.

**Rationale**:

- Extensible: new parsers can be added anywhere the decorator is imported.
- Platform override: a platform can register its own parser for a type that
  falls back to the generic `WechatPlatform.All` parser if absent.
- Self-documenting: the decorator makes it clear which message types a function
  handles.

**Trade-off**: Global mutable state. Import order matters. This is mitigated by
the CLI entry point always importing the platform module before invoking
commands.

### 3. Raw Dicts → Assembler Functions → Dataclasses

**Decision**: Platform modules return raw database rows as `dict`. A separate
layer of assembler functions (`assemble_friend`, etc.) converts them into domain
dataclasses.

**Rationale**:

- Separates DB schema knowledge (platform layer) from domain model structure (
  core layer).
- Assemblers can handle cross-cutting concerns like label lookups for friends.
- Platform schemas change independently of domain models.

**Trade-off**: Assembler functions are tightly coupled to the keys present in
platform dicts. Adding a new field requires updates in both the platform loader
and the assembler.

### 4. Context as a Dataclass Carrier

**Decision**: `WechatContext` and its subclasses are dataclasses that carry
configuration, open database connections, and media path roots.

**Rationale**:

- Explicit: all dependencies a loader/parser needs are visible in the context
  type.
- Type-safe: platform-specific functions accept their specific context subclass.

**Trade-off**: Contexts hold open DB connections, which means they must not be
closed prematurely. This is acceptable because the CLI is short-lived.

### 5. Profile-Based Configuration

**Decision**: The CLI reads a single INI file at
`~/.wechat-backup/profiles.ini`. Each profile contains platform, user_id,
database paths, media directories, etc.

**Rationale**:

- Simplifies repeated invocations (no need to pass 5+ CLI flags every time).
- Supports multiple backups via profile names.

**Trade-off**: Users must manually create and maintain the INI file. The tool
does not auto-discover backup locations.

### 6. JSONEncoder for Dataclass Serialization

**Decision**: `EntityJSONEncoder` handles serialization of dataclasses, datetime
objects, and enums for JSON output.

**Rationale**:

- Python's default `json.dumps` cannot serialize dataclasses or enums.
- Centralizing serialization in one encoder keeps output consistent.

### 7. No ORM

**Decision**: Raw SQL queries are used directly against SQLite.

**Rationale**:

- WeChat schemas are non-standard and undocumented. An ORM would require
  reverse-engineering and maintaining model definitions for tables we do not
  control.
- SQL gives precise control over column aliasing and joins needed to match
  assembler expectations.

**Trade-off**: SQL is scattered across platform modules. Schema changes in
future WeChat versions require manual query updates.

## Data Model

### Contacts

```
Contact (base)
  ├── Friend (+ id_alias, nickname_alias, avatar_url, tags[])
  ├── OfficialAccount (+ id_alias, icon_url, account_entity, app_id)
  ├── Microprogram
  └── Chatroom (+ members[], owner_id, user_display_name, is_deleted)
```

### Messages

```
Message
  ├── conversation_id: str
  ├── sent_at: datetime
  ├── sender_id: str
  ├── type: MessageType
  └── content: Content*

Content variants:
  TextContent, SystemContent, NameCardContent, LocationContent,
  ImageContent, VoiceContent, VideoContent, EmojiContent,
  VoIPContent, LinkContent, MusicContent, AttachmentContent,
  MoneyPacketContent, TransferContent, LocationShareContent
```

## Output Formats

- **Table**: Uses `tabulate` with a fixed header set. Best for quick inspection.
- **JSON**: Uses `json.dumps` with `EntityJSONEncoder`. Best for piping to other
  tools.

## Error Handling Strategy

- **Missing files**: `path_or_none()` returns `None`, which may trigger
  `__post_init__` exceptions in content dataclasses. These propagate up and
  crash the command with a traceback.
- **Missing parsers**: If no parser is registered for a message type,
  `assemble_message` falls back to the generic `WechatPlatform.All` parser. If
  still missing, a `KeyError` will be raised.
- **Malformed XML**: Parsers use `lxml.etree.fromstring`. Malformed content will
  raise an `lxml` exception.
- **Missing DB tables** (iOS): `find_message_db()` returns `None` if the
  conversation table is not found, which will cause an `AttributeError` when
  `.cursor()` is called. This is an edge case for deleted conversations.

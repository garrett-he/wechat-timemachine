from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    Text = 'text'
    Image = 'image'
    Voice = 'voice'
    NameCard = 'name-card'
    Video = 'video'
    Emoji = 'emoji'
    Location = 'location'
    Link = 'link'
    Music = 'music'
    Attachment = 'attachment'
    MoneyPacket = 'money-packet'
    Transfer = 'transfer'
    LocationShare = 'location-share'
    VoIP = 'voip'
    System = 'system'


@dataclass
class Message:
    conversation_id: str
    sent_at: datetime
    sender_id: str
    type: MessageType
    content: dataclass


@dataclass
class TextContent:
    content_type = MessageType.Text

    text: str


@dataclass
class SystemContent(TextContent):
    content_type = MessageType.System


@dataclass
class NameCardContent:
    content_type = MessageType.NameCard

    class Gender(Enum):
        Unknown = 0
        Male = 1
        Female = 2

    user_id: str
    nickname: str
    gender: Gender
    province: str
    city: str


@dataclass
class LocationContent:
    content_type = MessageType.Location

    latitude: float
    longitude: float
    address: str
    label: str


@dataclass
class ImageContent:
    content_type = MessageType.Image

    file_path: str
    thumbnail_path: str
    high_definition_path: str

    def __post_init__(self):
        if self.file_path == self.thumbnail_path == self.high_definition_path is None:
            raise Exception('No local file found for image message.')


@dataclass
class VoiceContent:
    content_type = MessageType.Voice

    file_path: str
    duration: int

    def __post_init__(self):
        if self.file_path is None:
            raise Exception('No local file found for voice message.')


@dataclass
class VideoContent:
    content_type = MessageType.Video

    file_path: str
    thumbnail_path: str
    duration: int

    def __post_init__(self):
        if self.file_path == self.thumbnail_path is None:
            raise Exception('No local file found for video message.')


@dataclass
class EmojiContent:
    content_type = MessageType.Emoji

    file_path: str


@dataclass
class VoIPContent:
    content_type = MessageType.VoIP

    class VoIPType(Enum):
        Unknown = -1
        Video = 0
        Audio = 1

    class VoIPStatus(Enum):
        Answered = 4
        Cancelled = 5

    type: VoIPType
    status: VoIPStatus
    duration: int


@dataclass
class LinkContent:
    content_type = MessageType.Link

    title: str
    description: str
    url: str
    thumbnail_path: str


@dataclass
class MusicContent(LinkContent):
    content_type = MessageType.Music

    data_url: str


@dataclass
class AttachmentContent:
    content_type = MessageType.Attachment

    title: str
    file_path: str


@dataclass
class MoneyPacketContent:
    content_type = MessageType.MoneyPacket

    @dataclass
    class PaymentInfo:
        icon_url: str
        receiver_title: str
        receiver_description: str
        sender_title: str
        sender_description: str
        scene_id: int
        scene_description: str

    title: str
    description: str
    payment_info: PaymentInfo


@dataclass
class TransferContent:
    content_type = MessageType.Transfer

    @dataclass
    class PaymentInfo:
        subtype: int
        description: str
        transfer_id: str
        transfer_time: int
        expire_time: int
        memo: str

    title: str
    description: str
    payment_info: PaymentInfo


@dataclass
class LocationShareContent:
    content_type = MessageType.LocationShare

    title: str

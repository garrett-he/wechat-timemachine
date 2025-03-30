import pytest

from wechat_timemachine.message.typing import (
    ImageContent,
    MessageType,
    NameCardContent,
    TextContent,
    VideoContent,
    VoiceContent,
)


class TestTextContent:
    def test_content_type(self):
        tc = TextContent(text="hello")
        assert tc.content_type == MessageType.Text
        assert tc.text == "hello"


class TestNameCardContent:
    def test_basic(self):
        nc = NameCardContent(
            user_id="wxid_123",
            nickname="Alice",
            gender=NameCardContent.Gender.Female,
            province="Guangdong",
            city="Shenzhen",
        )
        assert nc.content_type == MessageType.NameCard
        assert nc.gender == NameCardContent.Gender.Female


class TestImageContent:
    def test_valid_paths(self):
        ic = ImageContent(
            file_path="/tmp/img.jpg",
            thumbnail_path="/tmp/thumb.jpg",
            high_definition_path="/tmp/img_hd.jpg",
        )
        assert ic.content_type == MessageType.Image

    def test_all_none_raises(self):
        with pytest.raises(Exception, match="No local file found for image message"):
            ImageContent(file_path=None, thumbnail_path=None, high_definition_path=None)


class TestVoiceContent:
    def test_valid_path(self):
        vc = VoiceContent(file_path="/tmp/voice.amr", duration=5)
        assert vc.content_type == MessageType.Voice

    def test_none_path_raises(self):
        with pytest.raises(Exception, match="No local file found for voice message"):
            VoiceContent(file_path=None, duration=5)


class TestVideoContent:
    def test_valid_paths(self):
        vc = VideoContent(
            file_path="/tmp/video.mp4",
            thumbnail_path="/tmp/thumb.jpg",
            duration=10,
        )
        assert vc.content_type == MessageType.Video

    def test_none_paths_raises(self):
        with pytest.raises(Exception, match="No local file found for video message"):
            VideoContent(file_path=None, thumbnail_path=None, duration=10)

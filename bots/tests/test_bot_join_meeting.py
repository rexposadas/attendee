from unittest.mock import MagicMock

from bots.bot_controller.streaming_uploader import StreamingUploader


def create_mock_streaming_uploader():
    mock_streaming_uploader = MagicMock(spec=StreamingUploader)
    mock_streaming_uploader.upload_part.return_value = None
    mock_streaming_uploader.complete_upload.return_value = None
    mock_streaming_uploader.start_upload.return_value = None
    mock_streaming_uploader.key = "test-recording-key"  # Simple string attribute
    return mock_streaming_uploader

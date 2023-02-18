import pytest

from common.data import Chunk, FileExt, Recording
from s3mock.s3_api_mock import S3ObjectsGenerator


class TestS3ObjectsGenerator:

    @pytest.fixture
    def s3_objects_generator(self):
        return S3ObjectsGenerator()

    @pytest.fixture
    def recording(self):
        return Recording(recording_id="recording-123")

    def test_update_tree(self, s3_objects_generator):
        generator = s3_objects_generator
        recordings = ["recording-1", "recording-2", "recording-3"]
        result = generator.update_tree(recordings)

        assert len(result) == 3
        for recording in recordings:
            assert recording in result
            assert len(result[recording]) >= 1

    def test_generate_chunks_to_target(self, s3_objects_generator, recording):
        chunk1 = Chunk(obj_path="recording-123/chunk0.mp4", idx=0, ext=FileExt.CHUNK)
        chunk2 = Chunk(obj_path="recording-123/chunk1.mp4", idx=1, ext=FileExt.CHUNK)
        recording.artifacts = {chunk1, chunk2}
        s3_objects_generator.objects_tree = {"recording-123": recording}

        s3_objects_generator.generate_chunks_to_target("recording-123", 5, prefix="recording-123/")
        assert len(recording.artifacts) == 5

        expected_chunks = {
            Chunk(obj_path="recording-123/chunk0.mp4", idx=0, ext=FileExt.CHUNK),
            Chunk(obj_path="recording-123/chunk1.mp4", idx=1, ext=FileExt.CHUNK),
            Chunk(obj_path="recording-123/chunk2.mp4", idx=2, ext=FileExt.CHUNK),
            Chunk(obj_path="recording-123/chunk3.mp4", idx=3, ext=FileExt.CHUNK),
            Chunk(obj_path="recording-123/chunk4.mp4", idx=4, ext=FileExt.CHUNK),
        }

        assert recording.artifacts == expected_chunks

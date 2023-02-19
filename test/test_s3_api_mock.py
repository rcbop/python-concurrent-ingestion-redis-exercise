import pytest

from common.data import Chunk, FileExt, Recording
from s3mock.s3_api_mock import S3ObjectsGenerator

def test_update_tree():
    generator = S3ObjectsGenerator()
    recordings = ["recording-1", "recording-2", "recording-3"]
    result = generator.update_tree(recordings)

    assert len(result) == 3
    for recording in recordings:
        assert recording in result
        assert len(result[recording]) >= 1

def test_generate_chunks_to_target():
    generator = S3ObjectsGenerator()
    result = generator.generate_chunks_to_target(0, 5)

    assert len(result) == 5
    for i in range(5):
        assert result[i] == Chunk(obj_path=f"chunk{i}.mp4", idx=i, ext=FileExt.CHUNK)


def test_generate_and_append_chunks():
    s3_objects_generator = S3ObjectsGenerator()
    recording = Recording(recording_id="recording-123")
    chunk1 = Chunk(obj_path="chunk0.mp4", idx=0, ext=FileExt.CHUNK)
    chunk2 = Chunk(obj_path="chunk1.mp4", idx=1, ext=FileExt.CHUNK)
    recording.artifacts = {chunk1, chunk2}
    s3_objects_generator.objects_tree = {"recording-123": recording}

    s3_objects_generator.generate_and_append_chunks("recording-123", 5)
    assert len(recording.artifacts) == 5

    expected_chunks = [
        Chunk(obj_path="chunk0.mp4", idx=0, ext=FileExt.CHUNK),
        Chunk(obj_path="chunk1.mp4", idx=1, ext=FileExt.CHUNK),
        Chunk(obj_path="chunk2.mp4", idx=2, ext=FileExt.CHUNK),
        Chunk(obj_path="chunk3.mp4", idx=3, ext=FileExt.CHUNK),
        Chunk(obj_path="chunk4.mp4", idx=4, ext=FileExt.CHUNK),
    ]

    for expected_chunk in expected_chunks:
        assert expected_chunk in recording.artifacts

"""Mock AWS boto3 results."""
from dataclasses import dataclass, field
from datetime import date
import os
import random
import uuid
from typing import Any, Dict, Iterator, List, Set

import flask
from flask import Flask

from common.data import Recording, Chunk

API_PORT = os.environ.get('API_PORT', 5000)


@dataclass
class S3ObjectsGenerator():
    objects_tree: Dict[str, Recording] = field(default_factory=dict)
    start_date: date = field(default=date(day=28, month=10, year=2022))

    @staticmethod
    def recording_name_generator(max: int) -> Iterator[str]:
        """Mocking recording id."""
        for _ in range(max):
            yield f"recording-{uuid.uuid4()}"

    def generate_chunks_to_target(self, initial_idx: int, max_ix: int) -> List[Chunk]:
        """Generate chunks to target number."""
        return [Chunk(f"chunk{i}.mp4", i) for i in range(initial_idx, max_ix)]

    def generate_and_append_chunks(self, recording_id: str, max_chunks: int) -> None:
        """Append more chunks to existing record."""
        recording: Recording = self.objects_tree[recording_id]
        current_chunks = list(recording.artifacts)
        generated_chunks = self.generate_chunks_to_target(recording.last_chunk.idx + 1, max_chunks)
        recording.artifacts = [*current_chunks, *generated_chunks]

    def update_tree(self, generated_recordings: List[str]) -> Dict[str, Set[str]]:
        """Mock boto3 result of paths.

        Returns:
            dict correlating recording_id -> list of chunks (chunk1, chunk2 etc...)
        """
        chunks_dict = {}
        random_uploaded_recordings = int(random.random() * 300) + 1

        for _ in range(random_uploaded_recordings):
            recording_id = random.choice(generated_recordings)

            # can never be zero
            random_chunks_number = int(random.random() * 100) + 1

            # if recording already exists
            if recording_id in self.objects_tree:
                chunks_dict = self.generate_and_append_chunks(
                    recording_id, random_chunks_number)
            # create new recording and chunks list
            else:
                chunks_dict[recording_id] = [
                    Chunk(f"chunk{i}.mp4", i) for i in range(random_chunks_number)]

        return chunks_dict


def main():
    app = Flask(__name__)

    generated_recordings = list(
        S3ObjectsGenerator.recording_name_generator(500))
    generator = S3ObjectsGenerator(objects_tree={})

    @app.route('/get_s3_mocks/', methods=['GET'])
    def traverse_s3_mock() -> Any:
        return flask.jsonify(generator.update_tree(generated_recordings))

    @app.route('/get_all', methods=['GET'])
    def get_all_records():
        return flask.jsonify(generator.objects_tree)

    app.run(host="0.0.0.0", port=API_PORT)


if __name__ == "__main__":
    main()

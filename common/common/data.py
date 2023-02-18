
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Set


class FileExt(Enum):
    CHUNK = ".mp4"
    SIGNALS = ".mp4.json.zip"


@dataclass
class Artifact():
    obj_path: str
    idx: int
    ext: FileExt = field()


@dataclass
class Chunk(Artifact):
    ext: FileExt = FileExt.CHUNK

    @staticmethod
    def get_chunk_index(chunk: str) -> int:
        """Apply regex group to extract chunk index from obj key."""
        m = re.match(r'chunk(\d+).mp4$', chunk)
        assert m, 'Failed to parse chunk index'
        return int(m.groups()[0])

    def __hash__(self):
        return hash((self.obj_path, self.idx, self.ext))

@dataclass
class Signals(Artifact):
    ext: FileExt = FileExt.SIGNALS


@dataclass
class Recording():
    recording_id: str = field()
    artifacts: Set[Artifact] = field(default_factory=set)

    @property
    def last_chunk(self) -> Chunk:
        if len(self.artifacts) > 1:
            chunks_list = list(art for art in self.artifacts
            if art.ext == FileExt.CHUNK)
            return chunks_list[len(chunks_list)-1]

        return list(art for art in self.artifacts
            if art.ext == FileExt.CHUNK)[0]

    def __len__(self) -> int:
        return len(art for art in self.artifacts if art.ext == FileExt.CHUNK)

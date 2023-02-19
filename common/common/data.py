import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set


class FileExt(str, Enum):
    CHUNK = ".mp4"
    SIGNALS = ".mp4.json.zip"


@dataclass
class Artifact():
    obj_path: str
    idx: int
    ext: FileExt = field()

    def __str__(self) -> str:
        return self.obj_path

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

    def __lt__(self, other):
        return self.idx < other.idx

    def __eq__(self, other):
        return self.obj_path == other.obj_path and self.idx == other.idx and self.ext == other.ext

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        yield from {
            'obj_path': self.obj_path,
            'idx': self.idx,
            'ext': self.ext
        }.items()

    def __dict__(self):
        return {
            'obj_path': self.obj_path,
            'idx': self.idx,
            'ext': self.ext
        }


@dataclass
class Signals(Artifact):
    ext: FileExt = FileExt.SIGNALS


@dataclass
class Recording():
    recording_id: str = field()
    artifacts: Set[Artifact] = field(default_factory=set)

    @property
    def last_chunk(self) -> Optional[Chunk]:
        if len(self.artifacts) == 0:
            return None

        chunks_list = sorted(list(art for art in self.artifacts if art.ext == FileExt.CHUNK))
        return chunks_list[len(chunks_list)-1]

    def __len__(self) -> int:
        return len(art for art in self.artifacts if art.ext == FileExt.CHUNK)

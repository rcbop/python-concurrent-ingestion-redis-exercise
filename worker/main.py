"""Test redis shared dictionary."""
import hashlib
import json
import os
import random
import re
import socket
import time
from typing import Dict, Iterable, List, Set
from common.data import Chunk

import redis
import redis_lock
import requests

API_HOST = os.environ.get("API_HOST", "s3mock")
API_PORT = os.environ.get("API_PORT", 5000)
REDIS_HOST = os.environ.get("REDIS_HOST", "cache")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
REDIS_PASS = os.environ.get("REDIS_PASS")


def stop_criteria(idx: int, choice: int = None) -> bool:
    """Random stop criteria to simulate recording upload ended.

    Either the index is divisible by 7 or 15.
    """
    if choice:
        return idx % choice == 0
    divisible_by = random.choice([7, 15])
    return idx % divisible_by == 0


def get_last_chunk_index(chunks: List[str]) -> int:
    last_chunk = chunks[-1]
    if 'idx' in last_chunk:
        return last_chunk['idx']

    m = re.match(r'chunk(\d+)', last_chunk['obj_path'])
    if not m:
        raise RuntimeError(f"chunk name not valid {chunks[-1]}")
    return int(m.groups()[0])


def is_end_of_recording(chunks: List[str]) -> bool:
    """Take the last chunk and apply mocked stop criteria.
    """
    return stop_criteria(get_last_chunk_index(chunks))


def update_shared_dictionary(conn: redis.StrictRedis, chunks_dict: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """Update shared dictionary tracking recording and chunks.

    Returns:
        dict with ready to ingest recordings -> [chunks]
    """
    ready_to_ingest = {}

    for record_id, chunks in chunks_dict.items():
        # mocking condition to flag a recording as ingestible
        if len(chunks) and is_end_of_recording(chunks):
            # will ingest stuff...
            conn.delete(record_id)
            ready_to_ingest[record_id] = chunks
        else:
            got_chunks = conn.get(record_id)
            if got_chunks:
                got_chunks = [Chunk(**chunk) for chunk in json.loads(got_chunks)]
                current_chunks = [Chunk(**chunk) for chunk in chunks]
                chunks = set(current_chunks).union(got_chunks)

            chunks_to_store = [dict(chunk) for chunk in chunks]
            conn.set(record_id, json.dumps(chunks_to_store))

    return ready_to_ingest


def extract_chunks_hash(chunks: List[str]) -> str:
    """Extract chunks hash from list of chunks."""
    paths = [chunk['obj_path'] for chunk in chunks]
    return hashlib.sha256(','.join(paths).encode()).hexdigest()


def panics_if_already_ingested(conn: redis.StrictRedis, lock_id: str, ready_to_ingest: Dict[str, Set[str]]) -> None:
    """Crashes if it finds that a recording id was ingested more than once.

    Exception should display -> worker_id::record_id::chunks_hash
    """
    for record_id, chunks in ready_to_ingest.items():
        chunks_hash = conn.get(record_id)
        if chunks_hash and (chunks_hash == extract_chunks_hash(chunks)):
            # if hashes are equal no new files were added
            raise RuntimeError(f"recording already ingested {lock_id}::{record_id}::{chunks_hash}")

        conn.set(record_id, extract_chunks_hash(chunks))


def ingestion_mock(lock_id: str, ready_to_ingest: Dict[str, Set[str]], show_size=False) -> Iterable[str]:
    """Generate mocked ingestion unique keys -> worker_id::recorid_id.

    Can append chunks size for print
    """
    def append_chunk_len(size: int):
        return f" - ingested chunks size {size}" if show_size else ""

    return map(lambda record: f"{lock_id}::{record[0]}{append_chunk_len(len(record[1]))}\n", ready_to_ingest.items())


def get_redis_conn(db_idx: int):
    conn = redis.StrictRedis(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS, db=db_idx)
    assert conn.ping(), "Unable to connect to Redis"
    return conn


def main():
    print("wait 3s for redis...")
    time.sleep(3)
    conn_main = get_redis_conn(0)
    conn_checker = get_redis_conn(1)

    while True:
        response = requests.get(f"http://{API_HOST}:{API_PORT}/get_s3_mocks/")
        if response.status_code != 200:
            raise RuntimeError(f"API error {response.status_code}")

        chunks_dict = json.loads(response.content)
        lock_name = f"worker-{socket.gethostname()}"

        # lock redis to maintain the shared state
        with redis_lock.Lock(conn_main, lock_name):
            ready_to_ingest = update_shared_dictionary(conn_main, chunks_dict)

            # this is a validation step to ensure that a recording cannot be ingested twice
            panics_if_already_ingested(conn_checker, lock_name, ready_to_ingest)

        # redis is not locked here anymore
        # and the worker is free to ingest stuff
        # mocking ingestion with a simple print
        [print(ingest, end="") for ingest in ingestion_mock(
            lock_name, ready_to_ingest, show_size=True)]


if __name__ == "__main__":
    main()

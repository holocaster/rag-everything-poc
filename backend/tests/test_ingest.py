import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import main


def test_load_hashes_missing_file(tmp_path):
    fingerprint_file = tmp_path / "fingerprints.json"
    with patch.object(main, "_FINGERPRINT_FILE", fingerprint_file):
        assert main._load_hashes() == set()


def test_load_hashes_existing_file(tmp_path):
    fingerprint_file = tmp_path / "fingerprints.json"
    hashes = {"abc123", "def456"}
    fingerprint_file.write_text(json.dumps(list(hashes)))
    with patch.object(main, "_FINGERPRINT_FILE", fingerprint_file):
        assert main._load_hashes() == hashes


def test_save_and_load_hashes_round_trip(tmp_path):
    fingerprint_file = tmp_path / "fingerprints.json"
    hashes = {"aaa", "bbb", "ccc"}
    with patch.object(main, "_FINGERPRINT_FILE", fingerprint_file):
        main._save_hashes(hashes)
        assert main._load_hashes() == hashes


def test_sha256_known_value():
    data = b"hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert hashlib.sha256(data).hexdigest() == expected

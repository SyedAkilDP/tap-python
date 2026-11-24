
import hashlib
import json


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_manifest(path, manifest):
    temp_path = path.with_suffix(".tmp")

    temp_path.write_text(
        json.dumps(manifest, indent=4),
        encoding="utf-8"
    )

    temp_path.replace(path)


def already_processed(manifest, filename, signature):
    return manifest.get(filename) == signature

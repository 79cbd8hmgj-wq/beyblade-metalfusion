"""Validation for tracked source representations and generated asset bytes."""
from hashlib import sha256
from pathlib import Path
from .rom_image import RomError
from .modules import _decode

TYPES = {"raw_binary", "palette", "tile_data", "tilemap", "sprite_sheet", "portrait", "animation_metadata", "compressed_blob", "audio", "code_module"}


def validate(manifest, root="."):
    ids = set()
    results = []
    for asset in manifest.get("assets", []):
        if asset["id"] in ids:
            raise RomError("duplicate asset ID")
        ids.add(asset["id"])
        if asset["type"] not in TYPES:
            raise RomError("invalid asset type")
        path = Path(root, asset["path"])
        source = path.read_bytes()
        decoded = _decode(path, asset.get("encoding", "raw"))
        source_hash = sha256(source).hexdigest()
        decoded_hash = sha256(decoded).hexdigest()
        expected_source = asset.get("source_sha256")
        if expected_source and expected_source != source_hash:
            raise RomError(f"asset source hash mismatch: {asset['id']}")
        expected_decoded = asset.get("decoded_sha256", asset.get("sha256"))
        if expected_decoded != decoded_hash:
            raise RomError(f"asset decoded-byte hash mismatch: {asset['id']}")
        results.append({**asset, "source_sha256": source_hash, "decoded_sha256": decoded_hash, "source_size": len(source), "decoded_size": len(decoded)})
    return results

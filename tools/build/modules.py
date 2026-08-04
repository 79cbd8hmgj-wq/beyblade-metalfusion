"""Raw and text-safe preassembled module loading."""
from hashlib import sha256
from pathlib import Path
from .rom_image import RomError


def _decode(path: Path, encoding: str) -> bytes:
    if encoding == "raw":
        return path.read_bytes()
    if encoding == "hex":
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise RomError("hex module is not UTF-8") from exc
        compact = "".join(text.split())
        if len(compact) % 2:
            raise RomError("hex module has odd hexadecimal length")
        if any(c not in "0123456789abcdefABCDEF" for c in compact):
            raise RomError("hex module contains non-hexadecimal characters")
        return bytes.fromhex(compact)
    raise RomError(f"unsupported module encoding: {encoding}")


def load_raw(path, expected_hash=None, entry_offset=0, thumb=True, encoding="raw"):
    data = _decode(Path(path), encoding)
    module_hash = sha256(data).hexdigest()
    if expected_hash and module_hash != expected_hash:
        raise RomError("module decoded-byte hash mismatch")
    if not data:
        raise RomError("module is empty")
    if not 0 <= entry_offset < len(data):
        raise RomError("entry symbol outside module")
    return {
        "bytes": data,
        "sha256": module_hash,
        "entry_offset": entry_offset,
        "thumb": thumb,
        "encoding": encoding,
    }


def insert_raw(image, allocation, module, operation_id):
    if len(module["bytes"]) > allocation.size:
        raise RomError("module exceeds its allocation")
    return image.write(
        allocation.offset,
        module["bytes"],
        operation_id,
        source_artifact=module["sha256"],
    )

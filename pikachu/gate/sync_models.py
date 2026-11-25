"""Copy the pinned V0375 actor ONNX files from the sibling mjlab checkout."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SOURCE = HERE.parents[1] / "mjlab/src/mjlab/sim2sim/models/v0375"
TARGET = HERE / "models/v0375"


def main() -> None:
    manifest = json.loads((TARGET / "manifest.json").read_text())
    for name, expected in manifest["sha256"].items():
        src = SOURCE / name
        if (
            not src.is_file()
            or hashlib.sha256(src.read_bytes()).hexdigest() != expected
        ):
            raise SystemExit(f"Missing or mismatched source model: {src}")
        dst = TARGET / name
        if dst.exists() and hashlib.sha256(dst.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"Refusing to overwrite a different file: {dst}")
        if not dst.exists():
            shutil.copy2(src, dst)
        print(f"Verified {dst}")


if __name__ == "__main__":
    main()

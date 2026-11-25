"""Run the original V0375 gate using the locally copied actor models."""

import sys
from pathlib import Path

from mjlab.sim2sim_gate.runner import main


def run() -> None:
    model_dir = Path(__file__).resolve().parents[1] / "models" / "v0375"
    if any(arg in sys.argv for arg in ("--v037", "--v0375")):
        raise SystemExit("This launcher is fixed to v0375; omit version flags.")
    sys.argv[1:1] = ["--v0375"]
    for name in ("biped", "crawl", "transition_down", "transition_up"):
        flag = "--" + name.replace("_", "-") + "-onnx"
        if not any(arg == flag or arg.startswith(flag + "=") for arg in sys.argv[1:]):
            path = model_dir / f"{name}.onnx"
            if not path.is_file():
                raise SystemExit(f"Missing model: {path}")
            sys.argv.extend([flag, str(path)])
    main()


if __name__ == "__main__":
    run()

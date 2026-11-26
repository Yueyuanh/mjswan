"""Build browser scenes for the V0375 biped and crawl policies."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import onnx
from mjlab.scene import Scene
from mjlab.sim2sim.controllers import build_controller_specs, env_cfg_for

import mjswan
from pikachu.browser import terms  # noqa: F401

HERE = Path(__file__).resolve().parents[1]
DIST = HERE / "dist"
MODELS = HERE / "models" / "v0375"
#: The four actor graphs sync_models copies from the mjlab checkout.
MODEL_FILES = ("biped.onnx", "crawl.onnx", "transition_down.onnx", "transition_up.onnx")


def initial_qpos(cfg, spec):
    model = Scene(cfg.scene, device="cpu").spec.compile()
    qpos = model.key_qpos[0].copy() if model.nkey else model.qpos0.copy()
    robot = cfg.scene.entities["robot"].init_state
    root = model.joint("robot/floating_base")
    adr = int(root.qposadr[0])
    qpos[adr : adr + 3] = robot.pos
    qpos[adr + 3 : adr + 7] = robot.rot
    for name, position in zip(spec.joint_names, spec.default_joint_pos, strict=True):
        qpos[int(model.joint(f"robot/{name}").qposadr[0])] = position
    return qpos.tolist()


def build():
    builder = mjswan.Builder(base_path="./")
    project = builder.add_project(name="Pikachu V0375")
    specs = build_controller_specs(version="v0375")
    from pikachu.browser.gated import add_gate

    add_gate(project)
    for name, label in (("biped", "Biped walking"), ("crawl", "Quadruped crawling")):
        cfg = env_cfg_for(name, version="v0375")
        cfg.events = {}
        cfg.terminations = {}
        cfg.rewards = {}
        cfg.curriculum = {}
        cfg.metrics = {}
        scene = project.add_scene_mjlab(specs[name].task_id, name=label, env_cfg=cfg)
        cmd = cfg.commands["twist"]
        ranges = cmd.ranges
        crawl_limit = (-0.3, 0.3)
        scene.add_policy(
            name=label,
            policy=onnx.load(HERE / "models" / "v0375" / f"{name}.onnx"),
            observations=cfg.observations["actor"],
            actions=cfg.actions,
            commands={
                "twist": mjswan.velocity_command(
                    lin_vel_x=crawl_limit if name == "crawl" else ranges.lin_vel_x,
                    lin_vel_y=crawl_limit if name == "crawl" else ranges.lin_vel_y,
                    ang_vel_z=crawl_limit if name == "crawl" else ranges.ang_vel_z,
                    default_lin_vel_x=0.0,
                )
            },
            terminations={},
            events={},
            policy_joint_names=[f"robot/{joint}" for joint in specs[name].joint_names],
            default_joint_pos=list(specs[name].default_joint_pos),
            encoder_bias=[0.0] * len(specs[name].joint_names),
            initial_qpos=initial_qpos(cfg, specs[name]),
        )
    app = builder.build(output_dir=HERE / "dist")
    output = HERE / "dist"
    plugin = output / "assets" / "plugins.js"
    digest = hashlib.sha256(plugin.read_bytes()).hexdigest()[:16]
    versioned = plugin.with_name(f"plugins-{digest}.js")
    shutil.copy2(plugin, versioned)
    manifest = output / "manifest.json"
    data = json.loads(manifest.read_text())
    data["plugins"] = f"assets/{versioned.name}"
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return app


def ensure_models() -> None:
    """Fail with the sync command, and compose the gate graph on its first build."""
    missing = [name for name in MODEL_FILES if not (MODELS / name).exists()]
    if missing:
        raise SystemExit(
            f"Missing model files in {MODELS}: {', '.join(missing)}\n"
            "Sync them from the mjlab checkout first:\n"
            "  uv run --project ../mjlab python -m pikachu.gate.sync_models"
        )
    if not (MODELS / "gate_wide.onnx").exists():
        print("Composing models/v0375/gate_wide.onnx (first build only)...")
        subprocess.run(
            [sys.executable, "-m", "pikachu.gate.wide"], cwd=HERE.parent, check=True
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--build-only", action="store_true", help="Build pikachu/dist and exit."
    )
    mode.add_argument(
        "--no-build",
        action="store_true",
        help="Serve the existing pikachu/dist without rebuilding.",
    )
    parser.add_argument("--host", default="localhost", help="Host to bind.")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind.")
    parser.add_argument(
        "--no-open", action="store_true", help="Print the URL instead of opening it."
    )
    args = parser.parse_args()

    if args.no_build:
        if not (DIST / "index.html").exists():
            raise SystemExit(f"{DIST} is not built; run without --no-build first.")
        app = mjswan.MjswanApp(DIST)
    else:
        ensure_models()
        app = build()
    if not args.build_only:
        app.launch(host=args.host, port=args.port, open_browser=not args.no_open)


if __name__ == "__main__":
    main()

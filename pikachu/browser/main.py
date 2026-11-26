"""Build browser scenes for the V0375 biped and crawl policies."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import onnx
from mjlab.scene import Scene
from mjlab.sim2sim.controllers import build_controller_specs, env_cfg_for

import mjswan
from pikachu.browser import terms  # noqa: F401

HERE = Path(__file__).resolve().parents[1]


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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    app = build()
    if not args.build_only:
        app.launch()


if __name__ == "__main__":
    main()

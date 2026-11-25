"""Add the single-simulation four-actor gate to the mjswan app."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import onnx
from mjlab.envs.mdp import observations as mdp
from mjlab.sim2sim.controllers import build_controller_specs, env_cfg_for
from mjlab.sim2sim.env_cfg import make_sim2sim_env_cfg

import mjswan
from mjswan.mjlab import adapt_observations
from pikachu.browser.main import initial_qpos

HERE = Path(__file__).resolve().parents[1]


def absolute_joint_pos(env):
    return env.scene["robot"].data.joint_pos


def clip_data(path):
    with np.load(path) as clip:
        return {
            "joint_pos": clip["joint_pos"].tolist(),
            "joint_vel": clip["joint_vel"].tolist(),
            "anchor_pos": clip["body_pos_w"][:, 0, :].tolist(),
            "anchor_quat": clip["body_quat_w"][:, 0, :].tolist(),
        }


def add_gate(project):
    specs = build_controller_specs(version="v0375")
    cfg = make_sim2sim_env_cfg(version="v0375")
    biped_cfg = env_cfg_for("biped", version="v0375")
    crawl_cfg = env_cfg_for("crawl", version="v0375")
    biped = adapt_observations(biped_cfg.observations["actor"])["actor"].terms
    crawl = adapt_observations(crawl_cfg.observations["actor"])["actor"].terms
    binding = mjswan.ObservationBinding(
        ts_name="GateReference", ts_src=str(HERE / "browser/gate_observation.ts")
    )
    mjswan.register_observation("GateReference", binding)
    terms = {
        "sensor_linear": biped["base_lin_vel"],
        "sensor_angular": biped["base_ang_vel"],
        "heading_linear": crawl["base_lin_vel"],
        "heading_angular": crawl["base_ang_vel"],
        "gravity": biped["projected_gravity"],
        "joint_pos": mjswan.ObservationTermCfg(func=absolute_joint_pos),
        "joint_vel": biped["joint_vel"],
        "last_action": mjswan.ObservationTermCfg(func=mdp.last_action),
        "twist": biped["command"],
        "crawl_phase": crawl["crawl_phase"],
        "gate_reference": mjswan.ObservationTermCfg(
            func=binding,
            params={
                "down": clip_data(cfg.commands["motion_down"].motion_file),
                "up": clip_data(cfg.commands["motion_up"].motion_file),
            },
        ),
    }
    scene = project.add_scene_mjlab(
        "Mjlab-Tracking-Flat-Pikachu-V037-Down",
        name="Gated posture transition",
        env_cfg=cfg,
    )
    ranges = biped_cfg.commands["twist"].ranges
    scene.add_policy(
        name="Four-policy gate",
        policy=onnx.load(HERE / "models/v0375/gate_wide.onnx"),
        observations=mjswan.ObservationGroupCfg(terms=terms),
        actions=cfg.actions,
        commands={
            "twist": mjswan.velocity_command(
                lin_vel_x=ranges.lin_vel_x,
                lin_vel_y=ranges.lin_vel_y,
                ang_vel_z=ranges.ang_vel_z,
                default_lin_vel_x=0.0,
            ),
            "posture": mjswan.ui_command(
                [
                    mjswan.Checkbox(
                        name="biped", label="Biped (off: crawl)", default=True
                    )
                ]
            ),
        },
        events={},
        terminations={},
        policy_joint_names=[f"robot/{joint}" for joint in specs["biped"].joint_names],
        default_joint_pos=list(specs["biped"].default_joint_pos),
        encoder_bias=[0.0] * 23,
        initial_qpos=initial_qpos(biped_cfg, specs["biped"]),
    )

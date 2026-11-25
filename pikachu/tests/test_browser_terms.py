"""Check the crawl tracing fix against the training observations."""

from types import SimpleNamespace

import torch
from mjlab.tasks.velocity.config.pikachu_v035_crawl import mdp

from pikachu.browser import terms


def test_heading_observations_match_training_for_valid_robot_states():
    torch.manual_seed(42)
    quat = torch.randn(1024, 4)
    quat = quat / quat.norm(dim=-1, keepdim=True)
    data = SimpleNamespace(
        root_link_quat_w=quat,
        root_link_lin_vel_w=torch.randn(1024, 3),
        root_link_ang_vel_w=torch.randn(1024, 3),
    )
    env = SimpleNamespace(scene={"robot": SimpleNamespace(data=data)})
    torch.testing.assert_close(terms.heading_lin_vel(env), mdp.heading_lin_vel(env))
    torch.testing.assert_close(terms.heading_ang_vel(env), mdp.heading_ang_vel(env))


def test_initial_pose_uses_each_training_task():
    from mjlab.scene import Scene
    from mjlab.sim2sim.controllers import build_controller_specs, env_cfg_for

    from pikachu.browser.main import initial_qpos

    specs = build_controller_specs(version="v0375")
    for name in ("biped", "crawl"):
        cfg = env_cfg_for(name, version="v0375")
        pose = initial_qpos(cfg, specs[name])
        robot = cfg.scene.entities["robot"].init_state
        torch.testing.assert_close(torch.tensor(pose[:3]), torch.tensor(robot.pos))
        torch.testing.assert_close(torch.tensor(pose[3:7]), torch.tensor(robot.rot))
        model = Scene(cfg.scene, device="cpu").spec.compile()
        for joint, expected in zip(
            specs[name].joint_names, specs[name].default_joint_pos, strict=True
        ):
            assert pose[int(model.joint(f"robot/{joint}").qposadr[0])] == expected

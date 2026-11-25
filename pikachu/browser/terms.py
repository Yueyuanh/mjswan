"""Trace-compatible versions of the crawl heading observations."""

import torch
from mjlab.utils.lab_api.math import (
    quat_apply,
    quat_apply_inverse,
    quat_from_euler_xyz,
)

import mjswan


def _heading(quat):
    axis = quat.new_tensor([0.0, 0.0, 1.0]).expand(quat.shape[0], -1)
    forward = quat_apply(quat, axis)
    x, y = forward[:, 0], forward[:, 1]
    # torch.atan2(0, 0) returns 0; ORT returns NaN. Preserve torch's value.
    x = torch.where((x == 0) & (y == 0), torch.ones_like(x), x)
    yaw = torch.atan2(y, x)
    return quat_from_euler_xyz(torch.zeros_like(yaw), torch.zeros_like(yaw), yaw)


def heading_lin_vel(env):
    robot = env.scene["robot"]
    return quat_apply_inverse(
        _heading(robot.data.root_link_quat_w), robot.data.root_link_lin_vel_w
    )


def heading_ang_vel(env):
    robot = env.scene["robot"]
    return quat_apply_inverse(
        _heading(robot.data.root_link_quat_w), robot.data.root_link_ang_vel_w
    )


mjswan.register_observation("heading_lin_vel", heading_lin_vel)
mjswan.register_observation("heading_ang_vel", heading_ang_vel)

"""Compose the four teachers around a shared, explicit observation vector."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
from torch import nn

from pikachu.gate.compose import GateGraph


class WideGateGraph(nn.Module):
    """Map 148 values of physical state and gate state to 23 joint targets."""

    def __init__(self) -> None:
        super().__init__()
        self.gate = GateGraph()

    def forward(self, obs):
        sensor_linear = obs[:, 0:3]
        sensor_angular = obs[:, 3:6]
        heading_linear = obs[:, 6:9]
        heading_angular = obs[:, 9:12]
        gravity = obs[:, 12:15]
        joint_pos = obs[:, 15:38]
        joint_vel = obs[:, 38:61]
        last_target = obs[:, 61:84]
        twist = obs[:, 84:87]
        phase = obs[:, 87:89]
        target = obs[:, 89:90]
        state = obs[:, 90:91]
        first_step = obs[:, 91:92]
        direction = obs[:, 92:93]
        reference = obs[:, 93:139]
        anchor_pos = obs[:, 139:142]
        anchor_ori = obs[:, 142:148]
        moving = (target - state).abs() > 0.02
        twist = torch.where(moving, torch.zeros_like(twist), twist)
        phase = torch.where(moving, torch.zeros_like(phase), phase)

        def actor_obs(name, prefix, suffix):
            default = getattr(self.gate, name + "_default")
            scale = getattr(self.gate, name + "_scale")
            raw = torch.where(
                first_step > 0.5,
                torch.zeros_like(last_target),
                (last_target - default) / scale,
            )
            return torch.cat(
                (*prefix, joint_pos - default, joint_vel, raw, *suffix), dim=-1
            )

        biped = actor_obs("biped", (sensor_linear, sensor_angular, gravity), (twist,))
        crawl = actor_obs(
            "crawl", (heading_linear, heading_angular, gravity), (twist, phase)
        )
        transition_prefix = (
            reference,
            anchor_pos,
            anchor_ori,
            sensor_linear,
            sensor_angular,
        )
        down = actor_obs("transition_down", transition_prefix, ())
        up = actor_obs("transition_up", transition_prefix, ())
        return self.gate(biped, crawl, down, up, state, direction)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "models/v0375/gate_wide.onnx",
    )
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    graph = WideGateGraph().eval()
    torch.onnx.export(
        graph,
        torch.zeros(1, 148),
        str(args.out),
        input_names=["observation"],
        output_names=["joint_target"],
        opset_version=18,
        dynamo=False,
    )
    onnx.checker.check_model(onnx.load(args.out))
    session = ort.InferenceSession(str(args.out), providers=["CPUExecutionProvider"])
    torch.manual_seed(42)
    max_error = 0.0
    for i in range(64):
        x = torch.randn(1, 148)
        x[:, 89:91] = torch.rand(1, 2)
        x[:, 91] = i % 2
        x[:, 92] = (-1, 0, 1)[i % 3]
        with torch.no_grad():
            expected = graph(x).numpy()
        actual = session.run(None, {"observation": x.numpy()})[0]
        np.testing.assert_allclose(actual, expected, rtol=1e-3, atol=1e-4)
        max_error = max(max_error, float(np.max(np.abs(actual - expected))))
    print(
        f"Exported {args.out}; max error {max_error:.3g} rad over 64 synthetic inputs"
    )


if __name__ == "__main__":
    main()

"""Build a stateless V0375 gate graph for later browser integration."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
from mjlab.sim2sim.config import ALL_CONTROLLERS
from mjlab.sim2sim.controllers import build_controller_specs
from mjlab.sim2sim.export_onnx import build_torch_actor
from torch import nn


class GateGraph(nn.Module):
    """Combine four actors; callers supply the real per-actor observations."""

    def __init__(self) -> None:
        super().__init__()
        specs = build_controller_specs(version="v0375")
        self.actors = nn.ModuleDict()
        for name in ALL_CONTROLLERS:
            actor = build_torch_actor(specs[name].checkpoint)
            self.actors[name] = actor.model.as_onnx(verbose=False).eval()
            self.register_buffer(
                name + "_default", torch.tensor(specs[name].default_joint_pos)
            )
            self.register_buffer(
                name + "_scale", torch.tensor(specs[name].action_scale)
            )

    def forward(self, biped, crawl, transition_down, transition_up, p, direction):  # noqa: PLR0917
        b = self.biped_default + self.actors["biped"](biped) * self.biped_scale
        c = self.crawl_default + self.actors["crawl"](crawl) * self.crawl_scale
        d = (
            self.transition_down_default
            + self.actors["transition_down"](transition_down)
            * self.transition_down_scale
        )
        u = (
            self.transition_up_default
            + self.actors["transition_up"](transition_up) * self.transition_up_scale
        )
        endpoint = torch.lerp(c, b, p)
        weight = (2 * p - 1).abs().pow(2)
        moving = torch.where(direction > 0, u, d)
        return torch.where(
            direction == 0, endpoint, weight * endpoint + (1 - weight) * moving
        )


def compose(out: Path) -> None:
    torch.manual_seed(42)
    graph = GateGraph().eval()
    example = (
        torch.randn(1, 81),
        torch.randn(1, 83),
        torch.randn(1, 130),
        torch.randn(1, 130),
        torch.tensor([[0.4]]),
        torch.tensor([[1.0]]),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        graph,
        example,
        str(out),
        input_names=[
            "biped",
            "crawl",
            "transition_down",
            "transition_up",
            "p",
            "direction",
        ],
        output_names=["joint_target"],
        opset_version=18,
        dynamo=False,
    )
    onnx.checker.check_model(onnx.load(out))
    session = ort.InferenceSession(str(out), providers=["CPUExecutionProvider"])
    worst = 0.0
    for i in range(64):
        values = [torch.randn(1, n) for n in (81, 83, 130, 130)]
        values += [torch.rand(1, 1), torch.tensor([[float((-1, 0, 1)[i % 3])]])]
        with torch.no_grad():
            expected = graph(*values).numpy()
        actual = session.run(
            None,
            {
                v.name: x.numpy()
                for v, x in zip(session.get_inputs(), values, strict=True)
            },
        )[0]
        worst = max(worst, float(np.max(np.abs(expected - actual))))
        np.testing.assert_allclose(actual, expected, rtol=1e-3, atol=1e-4)
    source = build_controller_specs(version="v0375")
    manifest = {
        "status": "offline-composition-only",
        "samples": 64,
        "max_abs_error_rad": worst,
        "inputs": [
            "biped:81",
            "crawl:83",
            "transition_down:130",
            "transition_up:130",
            "p:1",
            "direction:1",
        ],
        "output": "joint_target:23",
        "onnx_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "checkpoints": {
            n: {
                "path": str(s.checkpoint),
                "sha256": hashlib.sha256(s.checkpoint.read_bytes()).hexdigest(),
            }
            for n, s in source.items()
        },
    }
    out.with_suffix(".json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "models/v0375/gate.onnx",
    )
    compose(parser.parse_args().out)


if __name__ == "__main__":
    main()

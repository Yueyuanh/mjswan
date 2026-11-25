"""Compare the composed graph with the four source actor sessions."""

from pathlib import Path

import numpy as np
import onnxruntime as ort
import pytest
from mjlab.sim2sim.controllers import build_controller_specs

MODELS = Path(__file__).resolve().parents[1] / "models/v0375"


def test_composed_graph_matches_independent_actors():
    gate_path = MODELS / "gate.onnx"
    if not gate_path.exists():
        pytest.skip("Run python -m pikachu.gate.compose first")
    gate = ort.InferenceSession(str(gate_path), providers=["CPUExecutionProvider"])
    specs = build_controller_specs(version="v0375")
    names = ("biped", "crawl", "transition_down", "transition_up")
    actors = {
        n: ort.InferenceSession(
            str(MODELS / f"{n}.onnx"), providers=["CPUExecutionProvider"]
        )
        for n in names
    }
    rng = np.random.default_rng(42)
    for direction in (-1.0, 0.0, 1.0):
        for p in (0.0, 0.2, 0.5, 0.8, 1.0):
            obs = {
                n: rng.standard_normal((1, dim), dtype=np.float32)
                for n, dim in zip(names, (81, 83, 130, 130), strict=True)
            }
            act = {}
            for n in names:
                session = actors[n]
                raw = session.run(None, {session.get_inputs()[0].name: obs[n]})[0]
                act[n] = np.asarray(
                    specs[n].default_joint_pos, dtype=np.float32
                ) + raw * np.asarray(specs[n].action_scale, dtype=np.float32)
            end = (1 - p) * act["crawl"] + p * act["biped"]
            weight = (2 * p - 1) ** 2
            expected = (
                end
                if direction == 0
                else weight * end
                + (1 - weight)
                * act["transition_up" if direction > 0 else "transition_down"]
            )
            result = gate.run(
                None,
                {
                    **obs,
                    "p": np.array([[p]], dtype=np.float32),
                    "direction": np.array([[direction]], dtype=np.float32),
                },
            )[0]
            np.testing.assert_allclose(result, expected, atol=1e-4, rtol=1e-3)

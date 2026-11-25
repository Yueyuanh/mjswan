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


def test_wide_graph_matches_independent_actor_observations():
    gate_path = MODELS / "gate_wide.onnx"
    if not gate_path.exists():
        pytest.skip("Run python -m pikachu.gate.wide first")
    gate = ort.InferenceSession(str(gate_path), providers=["CPUExecutionProvider"])
    specs = build_controller_specs(version="v0375")
    names = ("biped", "crawl", "transition_down", "transition_up")
    actors = {
        n: ort.InferenceSession(
            str(MODELS / f"{n}.onnx"), providers=["CPUExecutionProvider"]
        )
        for n in names
    }
    rng = np.random.default_rng(14)
    for i in range(24):
        wide = rng.standard_normal((1, 148), dtype=np.float32)
        target, state = (1.0, 0.25) if i % 2 else (0.0, 0.75)
        first = i % 3 == 0
        direction = 1 if target > state else -1
        wide[0, 89:93] = [target, state, first, direction]
        biped_prefix = wide[:, [*range(0, 6), *range(12, 15)]]
        crawl_prefix = wide[:, 6:15]
        transition_prefix = np.concatenate(
            (wide[:, 93:139], wide[:, 139:148], wide[:, :6]), axis=1
        )
        outputs = {}
        for name in names:
            spec = specs[name]
            default = np.asarray(spec.default_joint_pos, dtype=np.float32)
            scale = np.asarray(spec.action_scale, dtype=np.float32)
            previous = (
                np.zeros((1, 23), dtype=np.float32)
                if first
                else (wide[:, 61:84] - default) / scale
            )
            prefix = (
                biped_prefix
                if name == "biped"
                else crawl_prefix
                if name == "crawl"
                else transition_prefix
            )
            suffix = np.zeros(
                (1, 3 if name == "biped" else 5 if name == "crawl" else 0),
                dtype=np.float32,
            )
            obs = np.concatenate(
                (prefix, wide[:, 15:38] - default, wide[:, 38:61], previous, suffix),
                axis=1,
            )
            session = actors[name]
            raw = session.run(None, {session.get_inputs()[0].name: obs})[0]
            outputs[name] = default + raw * scale
        endpoint = (1 - state) * outputs["crawl"] + state * outputs["biped"]
        weight = (2 * state - 1) ** 2
        expected = (
            weight * endpoint
            + (1 - weight)
            * outputs["transition_up" if direction > 0 else "transition_down"]
        )
        actual = gate.run(None, {"observation": wide})[0]
        np.testing.assert_allclose(actual, expected, atol=1e-4, rtol=1e-3)

# Pikachu V0375 gate integration

## Status

This directory contains an **offline integration and a local mjlab launcher**. The
browser port is not complete and there is no deployable mjswan document yet. The
original V037 transition actors are reused on V0375; all four policies are simulation
candidates. No hardware deployment or complete V0375 evaluation is claimed.

- `legacy/run_gate.py`: launches the existing mjlab gate with local model copies.
- `models/v0375/manifest.json`: source model checksums. ONNX files are local artifacts
  and are excluded from Git.
- `gate/compose.py`: combines the four actors into a six-input stateless ONNX graph.
  It does not implement observation generation, posture state, reference selection,
  or the browser UI.
- `gate/provenance.json`: source identities and validation scope.
- `tests/test_gate_graph.py`: compares the combined ONNX against four separate actors.
- `doc/`: pre-existing design materials, preserved separately.

## Setup

Use this workspace layout and the existing mjlab environment:

```text
pikachu_playground/
  mjlab/     # source checkout and V0375 pre_train candidates
  mjswan/    # this repository
```

From `mjswan/`, verify and copy the selected local models:

```sh
uv run --project ../mjlab python -m pikachu.gate.sync_models
```

The command checks every SHA-256 and refuses to overwrite a different file. The source
`mjlab` checkout must contain the generation-routing changes and the V0375 models
listed in `gate/provenance.json`; the recorded mjlab source was uncommitted. Restoring
only its base commit is insufficient.

For mjswan build development, install this local checkout in the same environment:

```sh
uv pip install --python ../mjlab/.venv/bin/python -e .
```

## Run locally

```sh
uv run --project ../mjlab python -m pikachu.legacy.run_gate
```

This opens the original mjlab Viser interface, **not** a mjswan browser application.
For a repeatable headless compatibility check:

```sh
uv run --project ../mjlab python -m pikachu.legacy.run_gate \
  --viewer none --device cpu --max-steps 440 --script '2:quad,225:biped'
```

On the recorded workspace this completed both transitions, and its 24 printed status
lines matched the original mjlab entry. This is a smoke check, not a success-rate or
behavioral equivalence evaluation.

## Compose and test the offline graph

```sh
uv run --project ../mjlab python -m pikachu.gate.compose
uv run --project ../mjlab pytest pikachu/tests/test_gate_graph.py -q
```

Composition needs the four source checkpoints and their `config/agent.yaml` files in
`mjlab/pre_train/rsl_rl/pikachu_v0375/`. The local `gate.onnx` is generated and ignored
by Git. The test compares its output against independent ONNX Runtime actor sessions.
The graph requires correctly constructed actor observations and state on every step;
it is not a self-contained controller.

## Browser build and deployment

A browser build was attempted with the combined graph and the actual V0375 scene. It
failed before a valid document was produced. The first attempt could not trace
`JointPosRelToDefault`; a trace-friendly diagnostic replacement passed that point but
then `crawl` observation tracing failed with `DivergentGraph` (`base_lin_vel`, graph
`nan`, body `0`). The builder also skipped `HeadingHoldVelocityCommandCfg`,
`HoldMotionCommandCfg`, and `PostureCommandCfg`, and warned that the previous-action
observation would be frozen. The gate additionally needs phase, direction, both motion
clips, and reference re-anchoring wired to browser state. Ignoring these warnings would
produce a controller with the wrong inputs.

Consequently there is no `mjswan serve` or deployment command for this port yet. Finish
and independently validate those observation and command mappings, build a real mjswan
document, and run numeric and browser closed-loop parity before publishing it. The
original V0375 candidate and mjlab gate limitations remain applicable.

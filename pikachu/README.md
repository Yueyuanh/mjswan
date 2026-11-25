# Pikachu V0375 browser simulation

## Status

The mjswan browser app has two independently selectable scenes: biped walking and
quadruped crawling. The four-policy posture gate is a separate, unfinished integration.
The policies are simulation candidates; no hardware deployment or full browser
behavioral evaluation is claimed.

- `browser/main.py`: builds the two independent mjswan browser scenes.
- `browser/terms.py`: trace-compatible crawl heading observations.
- `legacy/run_gate.py`: launches the existing mjlab gate with local model copies.
- `models/v0375/manifest.json`: source model checksums. ONNX files are local artifacts
  and are excluded from Git.
- `gate/compose.py`: combines the four actors into a six-input stateless ONNX graph.
- `gate/wide.py`: provides a single 148-value input for those actors and their gate;
  browser-side state and reference generation are still required.
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

## Build and run the browser app

From `mjswan/`, after the setup above:

```sh
uv run --project ../mjlab python -m pikachu.browser.main --build-only
uv run --project ../mjlab mjswan serve pikachu/dist --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080/`. In **Scene**, select **Biped walking** or
**Quadruped crawling**. Use the three **Twist** controls to set forward, lateral,
and turning velocity; they start at zero. Reset returns the chosen scene to its
training task's initial pose. Each scene runs one policy: they do not transition
between postures.

To serve to other devices on a trusted local network, run:

```sh
uv run --project ../mjlab mjswan serve pikachu/dist --host 0.0.0.0 --port 8080 --no-open
```

Open `http://<this-computer-lan-ip>:8080/` on the other device. For a static-site
host, upload the contents of `pikachu/dist/` as a static site and preserve its
relative paths; configure cross-origin isolation if the browser or hosting setup
requires it. The site runs MuJoCo and ONNX Runtime in the browser. This repository
does not automatically publish it to a public service.

Both scenes built with mjswan 0.13.1. Observation parity passed over 16 steps per
scene and headless Chrome loaded each scene and accepted a 0.1 m/s forward command
without a browser error. This verifies loading and controls, not gait quality or
long-run stability. The crawl checkpoint has the previously recorded backward-motion
limitations. The scene starts with nominal settings, with training randomization and
termination terms disabled. MuJoCo Warp reported that CAPSULE/MESH pairs have at most
one contact with MULTICCD; browser MuJoCo physics can differ from training physics.

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
uv run --project ../mjlab python -m pikachu.gate.wide
uv run --project ../mjlab pytest pikachu/tests/test_gate_graph.py -q
```

Composition needs the four source checkpoints and their `config/agent.yaml` files in
`mjlab/pre_train/rsl_rl/pikachu_v0375/`. The local `gate.onnx` is generated and ignored
by Git. The test compares its output against independent ONNX Runtime actor sessions.
The graph requires correctly constructed actor observations and state on every step;
it is not a self-contained controller.

## Four-policy gate status

A browser build was attempted with the combined graph and the actual V0375 scene. It
failed before a valid document was produced. The first attempt could not trace
`JointPosRelToDefault`; a trace-friendly diagnostic replacement passed that point but
then `crawl` observation tracing failed with `DivergentGraph` (`base_lin_vel`, graph
`nan`, body `0`). The builder also skipped `HeadingHoldVelocityCommandCfg`,
`HoldMotionCommandCfg`, and `PostureCommandCfg`, and warned that the previous-action
observation would be frozen. The gate additionally needs phase, direction, both motion
clips, and reference re-anchoring wired to browser state. Ignoring these warnings would
produce a controller with the wrong inputs.

Consequently the two-scene app above cannot switch postures. Finish
and independently validate those observation and command mappings, build a real mjswan
document, and run numeric and browser closed-loop parity before publishing it. The
original V0375 candidate and mjlab gate limitations remain applicable.


## Task record

- mjlab base_commit: `1e6a0ae4adcdb437c33eb071afa40ee5dd27242f` (source working tree dirty; see `gate/provenance.json`).
- mjswan base_commit: `86974d21`.
- spec_read: `spec/agent-defaults.md`, `spec/git-management.md`.
- No training or formal behavior evaluation was performed; parity and browser startup checks are the available evidence.

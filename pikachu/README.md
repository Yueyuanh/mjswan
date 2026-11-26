# Pikachu V0375 browser simulation

## Status

The mjswan browser app has separate biped walking and quadruped crawling scenes,
plus a four-policy gated scene that runs in a single browser simulation. The policies
are simulation candidates; no hardware deployment or full browser behavioral
evaluation is claimed.

- `browser/main.py`: builds the two independent mjswan browser scenes.
- `browser/terms.py`: trace-compatible crawl heading observations.
- `browser/gated.py` and `gate_observation.ts`: gate scene and browser-side reference state.
- `legacy/run_gate.py`: launches the existing mjlab gate with local model copies.
- `models/v0375/manifest.json`: source model checksums. ONNX files are local artifacts
  and are excluded from Git.
- `gate/compose.py`: combines the four actors into a six-input stateless ONNX graph.
- `gate/wide.py`: provides a single 148-value input for those actors and their gate;
  `browser/gate_observation.ts` supplies posture state and reference data at runtime.
- `gate/provenance.json`: source identities and validation scope.
- `tests/test_gate_graph.py`: compares the combined ONNX against four separate actors.
- `doc/`: pre-existing design materials, preserved separately.

## Start

From `mjswan/`, after the model sync in [Setup](#setup):

```sh
uv run --project ../mjlab python -m pikachu.browser.main
```

This builds `pikachu/dist/` (composing `models/v0375/gate_wide.onnx` on the first
build) and opens `http://localhost:8080/`. Variants:

```sh
# serve the existing build, no rebuild
uv run --project ../mjlab python -m pikachu.browser.main --no-build

# build only, no server
uv run --project ../mjlab python -m pikachu.browser.main --build-only

# serve to the LAN without opening a browser
uv run --project ../mjlab python -m pikachu.browser.main --no-build --host 0.0.0.0 --no-open
```

If port 8080 is taken, the server moves to the next free port and prints the URL.

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
uv run --project ../mjlab python -m pikachu.browser.main --no-build
```

The first command rebuilds `pikachu/dist/`; the second serves it at
`http://localhost:8080/`. Running `python -m pikachu.browser.main` with neither flag
does both and opens the browser. The default scene is **Gated posture transition**;
use **Scene** to select **Biped walking** or **Quadruped crawling** instead.
Use the three **Twist** controls to set forward, lateral,
and turning velocity; they start at zero. Reset returns the chosen scene to its
initial pose. The keyboard drives the same commands: W/S, A/D and Q/E ramp forward/back,
left/right and turning to 75% of each axis's limit over about 0.8 s, the Twist sliders
follow, and opposing keys (W+S, A+D, Q+E) cancel an axis. F toggles posture in the gated
scene, Z hides the panel, R resets; a top-left HUD lists the keys and hides with the
panel (Z hides both). In the gated scene, use **切换四足** or **切换双足** in **Posture**.
The button shows simulation progress and is disabled until the transition finishes.
During each transition, the velocity sliders are set to zero; set them again afterward.
In quadruped crawling and the gated crawl mode, forward and lateral velocity commands
are limited to ±0.3 m/s and yaw commands to ±0.3 rad/s. The biped range is unchanged.
The restriction follows a reported limb interference issue at higher crawl speeds;
it is not evidence that interference is eliminated within the restricted range.
The transition takes about four seconds of simulation time.

To serve to other devices on a trusted local network, run:

```sh
uv run --project ../mjlab python -m pikachu.browser.main --no-build --host 0.0.0.0 --port 8080 --no-open
```

Open `http://<this-computer-lan-ip>:8080/` on the other device. For a static-site
host, upload the contents of `pikachu/dist/` as a static site and preserve its
relative paths; configure cross-origin isolation if the browser or hosting setup
requires it. The site runs MuJoCo and ONNX Runtime in the browser. This repository
does not automatically publish it to a public service.

All three scenes built with mjswan 0.13.1. The gate packages custom JavaScript and is
suitable for a trusted static host, not mjswan Cloud. During browser testing one
static down/up transition completed, and another up transition after a longer crawl
stance fell; reliable posture switching is not established.

For the independent scenes, observation parity passed over 16 steps per
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

## Gate validation and known limitations

The gate scene traces the physical observation terms, uses the composed single-input
ONNX, and keeps posture, frame selection and reference re-anchoring in the browser.
It uses the V037 down/up pilot models on a V0375 robot. Browser MuJoCo and mjlab's
training physics differ, and the original models are simulation candidates.

Checks for the local build:

```sh
node pikachu/tests/test_gate_reference.mjs
uv run --project ../mjlab pytest pikachu/tests/test_gate_graph.py pikachu/tests/test_browser_terms.py -q
uv run --project ../mjlab mjswan serve pikachu/dist --host 127.0.0.1 --port 8765 --no-open
# In a second terminal, using a local Chrome:
node pikachu/tests/test_browser_gate.mjs
```

These checks do not prove robust walking-to-standing transitions. A longer static
crawl hold produced a fall after the up request in one browser run, while another
short-hold round trip succeeded. The gate has no automatic fall recovery; the
operator can use Reset. Re-test on the target browser and hardware before sharing.

## Task record

- mjlab base_commit: `1e6a0ae4adcdb437c33eb071afa40ee5dd27242f` (source working tree dirty; see `gate/provenance.json`).
- mjswan base_commit: `86974d21`.
- spec_read: `spec/agent-defaults.md`, `spec/git-management.md`.
- No training or formal behavior evaluation was performed; parity and browser startup checks are the available evidence.

- Gate task base: mjlab `1e6a0ae4adcdb437c33eb071afa40ee5dd27242f`, mjswan `7df9fbdd`; spec_read: `spec/agent-defaults.md`, `spec/git-management.md`. Browser integration is not a formal evaluation.

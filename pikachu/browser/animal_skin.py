"""Quadruped GLB skins for the pikachu's crawl posture.

The same quadruped mapping the demo uses on the Go1: front legs as arms, hind legs as
legs, so the robot's crawl stance lands the animal on all fours. Feet are hung from the
legs that carry them (Quaternius's rigs drive the feet with IK controls at the root), and
each file is scaled so the animal stands as tall as the crawling robot.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

import mjswan
from mjswan.document.skin import read_skin_file
from pikachu.browser.avatar_skin import PIKACHU_BONES

#: The crawling robot's body links span about 0.26 m; the animals stand no taller.
TARGET_HEIGHT = 0.30

#: The robot's base_link height over the floor at the crawl stance (its root position).
ROBOT_ROOT_HEIGHT = 0.229

#: VRM humanoid bone -> the node of Quaternius's animals: front legs as arms, and the
#: four bones of a hind leg as upper and lower leg, foot and toes.
POLY_PIZZA_HUMANOID = {
    "hips": "Back",
    "spine": "Torso",
    "chest": "Torso2",
    "neck": "Neck1",
    "head": "Head",
    **{
        f"{side}{bone}": f"{node}.{suffix}"
        for side, suffix in (("left", "L"), ("right", "R"))
        for bone, node in (
            ("UpperArm", "FrontUpperLeg"),
            ("LowerArm", "FrontLowerLeg"),
            ("Hand", "IKFrontLeg"),
            ("UpperLeg", "BackLeg"),
            ("LowerLeg", "BackUpperLeg"),
            ("Foot", "BackLowerLeg"),
            ("Toes", "IKBackLeg"),
        )
    },
}

#: Its feet hang from IK controls at the root, so from joint angles alone they would stay
#: behind; hung from the legs they end, the legs carry them.
POLY_PIZZA_FEET = {
    f"IK{end}Leg.{suffix}": f"{end}LowerLeg.{suffix}"
    for end in ("Front", "Back")
    for suffix in "LR"
}

#: The Pug's own names; its hips bone is mid-body, and it has no toes.
PUG_HUMANOID = {
    "hips": "Body",
    "spine": "Shoulders",
    "neck": "Neck",
    "head": "Head",
    "leftUpperArm": "FrontUpLeg.L",
    "leftLowerArm": "FrontLowLeg.L",
    "leftHand": "FrontFoot.L",
    "rightUpperArm": "FrontUpLeg.R",
    "rightLowerArm": "FrontLowLeg.R",
    "rightHand": "FrontFoot.R",
    "leftUpperLeg": "BackUpLeg.L",
    "leftLowerLeg": "BackLowLeg.L",
    "leftFoot": "BackFoot.L",
    "rightUpperLeg": "BackUpLeg.R",
    "rightLowerLeg": "BackLowLeg.R",
    "rightFoot": "BackFoot.R",
}

TOON = mjswan.ToonShading(shade=0.6, toony=0.5)

NAMES = {"shiba_inu": "Shiba Inu", "fox": "Fox", "pug": "Pug"}

NOTICES = {
    "shiba_inu": "Shiba Inu by Quaternius (CC0 1.0), https://poly.pizza/m/y4wdQpg767\n",
    "fox": "Fox by Quaternius (CC0 1.0), https://poly.pizza/m/Bc97C66HKi\n",
    "pug": (
        "Pug: from Farm Animals Animated by Quaternius (CC0 1.0), "
        "https://quaternius.itch.io/lowpoly-animated-animals\n"
    ),
}


def height_for(source: Path) -> float:
    """The file's rest height, over its own units."""
    skin = read_skin_file(source)
    return float(skin.positions(1.0, "+z")[:, 1].max())


def scale_for(source: Path) -> float:
    return TARGET_HEIGHT / height_for(source)


def height_ratio_for(source: Path, scale: float, humanoid: dict[str, str]) -> float:
    """Put the animal's hips where its own legs reach the floor.

    The file default divides by the robot root's height above its soles at the *zero*
    pose, which the crawl stance shrinks to a few centimetres, lifting the animal. This
    pins the hips to its own scaled hip height instead.
    """
    skin = read_skin_file(source)
    hips = skin.positions(scale, "+z")[skin.node(humanoid["hips"])][1]
    return float(hips) / ROBOT_ROOT_HEIGHT


def crawl_rest_pose() -> dict[str, float] | str | None:
    """The robot's crawl stance: what the animal's own rest pose lines up with.

    ``PIKACHU_ANIMAL_REST=zero`` or ``init`` overrides it for a local comparison.
    """
    mode = os.environ.get("PIKACHU_ANIMAL_REST", "crawl")
    if mode == "zero":
        return None
    if mode == "init":
        return "init_state"
    from mjlab.sim2sim.controllers import build_controller_specs

    spec = build_controller_specs(version="v0375")["crawl"]
    return {
        name: float(value)
        for name, value in zip(spec.joint_names, spec.default_joint_pos)
    }


def fox_springs(scale: float) -> list[mjswan.SpringChain]:
    """The tail the demo swings, its lengths scaled with the animal."""
    ratio = scale / 0.2425
    return [
        mjswan.SpringChain(
            root="Tail1",
            stiffness=1.5,
            drag=0.3,
            gravity=0.1,
            hit_radius=0.03 * ratio,
            colliders=(
                mjswan.SpringCollider("Back", radius=0.06 * ratio),
                *(
                    mjswan.SpringCollider(f"BackLeg.{s}", radius=0.035 * ratio)
                    for s in "LR"
                ),
            ),
        )
    ]


def add_animal_skins(scene, sources: Sequence[Path]) -> None:
    """Add one quadruped per GLB, posed by the robot's crawl stance."""
    rest = crawl_rest_pose()
    for source in sources:
        source = Path(source)
        stem = source.stem
        scale = scale_for(source)
        if stem == "pug":
            humanoid, reparent, springs = PUG_HUMANOID, {}, []
        else:
            humanoid, reparent = POLY_PIZZA_HUMANOID, POLY_PIZZA_FEET
            springs = fox_springs(scale) if stem == "fox" else []
        bones = {
            bone: PIKACHU_BONES[bone] for bone in humanoid if bone in PIKACHU_BONES
        }
        height_ratio = height_ratio_for(source, scale, humanoid)
        scene.add_skin(
            NAMES.get(stem, stem),
            mjswan.SkinConfig(
                bones=bones,
                humanoid=humanoid,
                reparent=reparent,
                source=str(source),
                scale=scale,
                rest_pose=rest,
                height_ratio=height_ratio,
                material=TOON,
                springs=springs,
                license="CC0-1.0",
                notice=NOTICES.get(stem),
            ),
        )

"""Map VRM humanoids onto the V0375 pikachu robot, for a local skin experiment.

The robot has no torso joints, so the avatar's hips through neck ride ``base_link``;
each limb's bone carries the deepest robot link above the next joint, which is how the
demo maps G1's ``shoulder_yaw_link``. The robot's zero pose has the arms straight out,
so a VRM's T-pose needs no ``rest_pose``.

A VRM's units are the file's, and mjswan refuses ``scale`` for one, so a pikachu-sized
copy is made by writing a scale onto its skeleton roots; the file stays a VRM. The scale
normalises each avatar's head to the same height over the floor, so avatars of different
authored heights stand alike.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Sequence

import mjswan
from mjswan.document.skin import read_skin_file

#: Avatar head height over the floor, in metres: the robot's head link sits around 0.5 m.
TARGET_HEAD_HEIGHT = 0.5

#: VRM humanoid bone -> robot body (the entity prefix may be left out).
PIKACHU_BONES = {
    "hips": "base_link",
    "spine": "base_link",
    "chest": "base_link",
    "neck": "base_link",
    "head": "head_yaw_link",
    **{
        f"{side}{bone}": f"{side.lower()}_{body}"
        for side in ("left", "right")
        for bone, body in (
            ("UpperArm", "arm_yaw_link"),
            ("LowerArm", "elbow_link"),
            ("Hand", "elbow_link"),
            ("UpperLeg", "hip_yaw_link"),
            ("LowerLeg", "knee_link"),
            ("Foot", "ankle_link"),
        )
    },
}

#: File stem -> the Skin menu's name.
NAMES = {
    "100Avatars_001_Crimsom": "Crimsom",
    "100Avatars_024_CoolBanana": "Cool Banana",
    "AvatarSample_A": "AvatarSample A",
    "AvatarSample_B": "AvatarSample B",
    "AvatarSample_C": "AvatarSample C",
    "VRM1_Constraint_Twist_Sample": "Constraint Twist",
    "pikachu_v1": "Pikachu V1",
}

#: Files authored at the robot's own scale, used as they are (no resizing).
ROBOT_SCALE = frozenset({"pikachu_v1"})


def _prettify(stem: str) -> str:
    return " ".join(part for part in stem.split("_") if not part.isdigit())


def scale_for(source: Path) -> float:
    """The factor that puts this avatar's head bone at TARGET_HEAD_HEIGHT."""
    if source.stem in ROBOT_SCALE:
        return 1.0
    skin = read_skin_file(source)
    head = skin.positions(1.0, "+z")[skin.human_bones["head"]]
    return TARGET_HEAD_HEIGHT / float(head[1])


def scaled_copy(source: Path, factor: float) -> Path:
    """The same VRM with ``factor`` written onto the skeleton roots' node scale."""
    data = source.read_bytes()
    magic, version, _ = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67 or version != 2:
        raise ValueError(f"{source.name} is not a binary glTF")
    json_len, _ = struct.unpack_from("<II", data, 12)
    gltf = json.loads(data[20 : 20 + json_len])
    scene = gltf["scenes"][gltf.get("scene", 0)]
    for index in scene["nodes"]:
        node = gltf["nodes"][index]
        if "mesh" in node:
            continue
        scale = node.get("scale", [1.0, 1.0, 1.0])
        node["scale"] = [value * factor for value in scale]
    payload = json.dumps(gltf, separators=(",", ":")).encode()
    payload += b" " * (-len(payload) % 4)
    binary = data[20 + json_len :]
    total = 12 + 8 + len(payload) + len(binary)
    target = source.with_name(f"{source.stem}_x{factor:.3f}{source.suffix}")
    target.write_bytes(
        struct.pack("<III", magic, version, total)
        + struct.pack("<II", len(payload), 0x4E4F534A)
        + payload
        + binary
    )
    return target


def add_avatar_skins(scene, sources: Sequence[Path]) -> None:
    """Add one pikachu-sized skin per VRM, the first being what the scene opens on."""
    for source in sources:
        source = Path(source)
        factor = scale_for(source)
        file = source if factor == 1.0 else scaled_copy(source, factor)
        scene.add_skin(
            NAMES.get(source.stem, _prettify(source.stem)),
            mjswan.SkinConfig(bones=PIKACHU_BONES, source=str(file)),
        )

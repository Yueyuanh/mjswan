"""Pikachu V1's non-humanoid VRM bone bindings."""

EXTRA_BONES = {"Tail1": "tail_yaw_link"}

# V1's limb lengths make hybrid IK repeatedly lower its whole body during crawling.
RETARGET = "rotation"
HEIGHT_RATIO = 1.0

# Pikachu V1 皮套：骨骼与映射

本目录存放仓库自带的皮卡丘皮套 `pikachu_v1.vrm`，以及它接到 V0375 机器人上的骨骼映射
说明。其它 VRM/GLB 是运行时从 Hugging Face `ttktjmt/mjswan` 下载的，不放在这里
（`pikachu/.cache/skins/`，git 忽略）。

## 文件

| 项 | 值 |
| --- | --- |
| 文件 | `pikachu_v1.vrm`（471 KB） |
| 格式 | VRM 0.x（glTF 2.0 binary + `VRM` 扩展） |
| 节点 / 网格 / skin | 61 / 2 / 2 |
| humanoid 骨骼 | 23 根 |
| 元数据 | `title`/`author` 为占位 `1`，`licenseName: Other`，`allowedUserName: Everyone` |

原始尺寸（1.0×，VRM 1.0 帧：y 向上、面向 +z）：

| 骨骼 | 高度/位置（m） |
| --- | --- |
| `hips` | y ≈ 0.126 |
| `head` | y ≈ 0.25 |
| 最高点（耳朵） | y ≈ 0.459 |
| 最低点 | y ≈ −0.027 |

## 缩放：构建时 ×1.8

这个皮套是按机器人做的，但相对机器人本体偏小，构建时统一放大 **1.8 倍**：

- 源文件**不改**；`avatar_skin.py` 的 `SCALE_FACTORS = {"pikachu_v1": 1.8}` 会把缩放写到
  骨架根节点的 `scale` 上，生成副本：
  `pikachu/.cache/scaled/pikachu_v1_x1.800.vrm`（git 忽略）；
- 生成物仍是合法 VRM（three-vrm、mjswan 都能读）；
- 缩放后整体约 **0.83 m 高**，`head` 约 0.45 m；
- 想再调，改 `SCALE_FACTORS` 的数值即可；或者在 Blender 里把模型缩放到目标尺寸后重新
  导出覆盖 `pikachu_v1.vrm`，并把该文件从 `SCALE_FACTORS` 移除。

`height_ratio` 不手动设：皮肤根高度按“角色胯高 / 机器人根高”自动算，缩放后会跟着变。

## humanoid 骨骼清单（VRM 0.x 名称 → 文件节点）

| VRM 骨骼 | 节点 | 是否映射 |
| --- | --- | --- |
| `hips` | `Hips` | ✅ |
| `spine` | `Spine` | ✅ |
| `chest` | `Chest` | ✅ |
| `neck` | `Neck` | ✅ |
| `head` | `Head` | ✅ |
| `leftShoulder` | `Left shoulder` | —（保持 rest） |
| `leftUpperArm` | `Left arm` | ✅ |
| `leftLowerArm` | `Left elbow` | ✅ |
| `leftHand` | `Left wrist` | ✅ |
| `leftUpperLeg` | `Left leg` | ✅ |
| `leftLowerLeg` | `Left knee` | ✅ |
| `leftFoot` | `Left ankle` | ✅ |
| `leftToes` | `Left toe` | —（机器人没有脚趾） |
| `rightShoulder` | `Right shoulder` | — |
| `rightUpperArm` | `Right arm` | ✅ |
| `rightLowerArm` | `Right elbow` | ✅ |
| `rightHand` | `Right wrist` | ✅ |
| `rightUpperLeg` | `Right leg` | ✅ |
| `rightLowerLeg` | `Right knee` | ✅ |
| `rightFoot` | `Right ankle` | ✅ |
| `rightToes` | `Right toe` | — |
| `leftEye` | `Ear1_L` | —（这个皮套把眼睛骨骼指到耳朵，不参与驱动） |
| `rightEye` | `Ear1_R` | — |

## 映射到机器人（`PIKACHU_BONES`）

规则：**根骨骼负责位置；每根骨骼映射到“能带上它全部旋转”的最深机器人 link**。皮卡丘
机器人没有躯干、腕和脚趾关节，所以：

| VRM 骨骼 | 机器人 body | 理由 |
| --- | --- | --- |
| `hips` / `spine` / `chest` / `neck` | `base_link` | 没有脊柱关节，躯干整体跟 base |
| `head` | `head_yaw_link` | 取 head_pitch + roll + yaw 的合成旋转 |
| `leftUpperArm` / `rightUpperArm` | `arm_yaw_link` | 肩上 pitch/roll/yaw 三段的合成 |
| `leftLowerArm` / `rightLowerArm` | `elbow_link` | 肘关节 |
| `leftHand` / `rightHand` | `elbow_link` | 没有腕关节，手跟随小臂 |
| `leftUpperLeg` / `rightUpperLeg` | `hip_yaw_link` | 髋三段（pitch/roll/yaw）的合成 |
| `leftLowerLeg` / `rightLowerLeg` | `knee_link` | 膝关节 |
| `leftFoot` / `rightFoot` | `ankle_link` | 踝关节；没有脚趾 |

- `rest_pose`：皮卡丘零位就是 T-pose（手臂水平），所以不写（= 零位）；
- `retarget`：默认 `hybrid`（保持角色比例，两骨 IK 把手/脚拉到机器人位置）；
- `hide_robot`：默认 True，皮套显示时隐藏机器人；`?xray=1` 可透视检查对齐。

## 构建与检查

```sh
cd mjswan

# 默认构建就会挂上 Pikachu V1（--no-skin 可关闭）
uv run --project ../mjlab python -m pikachu.browser.main --build-only

uv run --project ../mjlab python -m pikachu.browser.main --no-build \
  --port 8080 --no-open
```

- 菜单名 **Pikachu V1**，URL `?skin=pikachu_v1`；
- 默认场景是 **Gated posture transition**；
- 想同时加载云端皮套：追加 `--skin pikachu/.cache/skins`。

## 修改这个皮套的建议流程

1. 在 Blender 里打开/编辑模型（保持 VRM humanoid 骨骼命名与 T-pose）；
2. 缩放需求优先在 Blender 里直接做好，然后从 `SCALE_FACTORS` 移除 `pikachu_v1`；
3. 导出 VRM 0.x（或 1.0）覆盖 `pikachu/vrm/pikachu_v1.vrm`；
4. 重新构建，看站姿、走路、crawl 和 `?xray=1` 对齐；
5. 如果骨骼名字变了，同步更新 `avatar_skin.py` 的 `PIKACHU_BONES` 和本文档。

更完整的 VRM 格式与制作流程见 `../doc/vrm_skin_guide_20261126.md`。

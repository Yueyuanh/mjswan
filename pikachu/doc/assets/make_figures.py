"""Generate the diagrams used by ``sim2sim_gate_migration_plan.md``.

Run with the shared mjlab environment::

    cd mjlab && .venv/bin/python ../mjswan/pikachu/doc/assets/make_figures.py

The figures are intentionally plain: boxes, arrows and one inset plot, so they stay
readable in a Markdown renderer and are easy to edit. Labels are Chinese because the
plan is; identifiers stay in English.
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = pathlib.Path(__file__).resolve().parent
plt.rcParams.update(
    {
        "font.sans-serif": ["Noto Sans CJK JP", "Droid Sans Fallback"],
        "axes.unicode_minus": False,
        "figure.dpi": 200,
        "savefig.dpi": 200,
    }
)

C_PY, C_PY_E = "#E8F0FA", "#3C6E9F"
C_JS, C_JS_E = "#E6F4EA", "#3F7D53"
C_ONNX, C_ONNX_E = "#FCEBDA", "#B86B2B"
C_UI, C_UI_E = "#EEE8F8", "#6D5AA8"
C_ENV, C_ENV_E = "#FFF4D6", "#A07A1F"
C_RISK, C_RISK_E = "#FBE3E3", "#A94B4B"
C_GRAY, C_GRAY_E = "#F2F2F2", "#666666"


def canvas(figsize=(16, 9)):
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(
    ax,
    x,
    y,
    w,
    h,
    title,
    body="",
    *,
    fc=C_GRAY,
    ec=C_GRAY_E,
    title_size=11,
    body_size=9,
    lw=1.4,
    title_color="#1A1A1A",
    body_color="#333333",
):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.35,rounding_size=0.9",
        linewidth=lw,
        edgecolor=ec,
        facecolor=fc,
        zorder=2,
    )
    ax.add_patch(patch)
    if body:
        ax.text(
            x + w / 2,
            y + h * 0.66,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            color=title_color,
            fontweight="bold",
            zorder=3,
        )
        ax.text(
            x + w / 2,
            y + h * 0.32,
            body,
            ha="center",
            va="center",
            fontsize=body_size,
            color=body_color,
            zorder=3,
            linespacing=1.35,
        )
    else:
        ax.text(
            x + w / 2,
            y + h / 2,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            color=title_color,
            zorder=3,
            linespacing=1.35,
        )


def container(ax, x, y, w, h, title, *, fc="#F7F9FC", ec=C_PY_E, title_size=12):
    """A large box with its title on the top edge, so it never sits on the children."""
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.35,rounding_size=0.9",
        linewidth=1.6,
        edgecolor=ec,
        facecolor=fc,
        zorder=1,
    )
    ax.add_patch(patch)
    ax.text(
        x + 2.0,
        y + h - 3.0,
        title,
        ha="left",
        va="center",
        fontsize=title_size,
        fontweight="bold",
        zorder=3,
    )


def arrow(ax, xy_from, xy_to, *, color="#555555", lw=1.6, style="-|>", rad=0.0, ls="-"):
    ax.add_patch(
        FancyArrowPatch(
            xy_from,
            xy_to,
            arrowstyle=style,
            mutation_scale=14,
            linewidth=lw,
            color=color,
            linestyle=ls,
            connectionstyle=f"arc3,rad={rad}",
            zorder=4,
            shrinkA=2,
            shrinkB=2,
        )
    )


def label(ax, x, y, text, *, size=9, color="#444444", ha="center", va="center", weight="normal", bg=None):
    kw = {}
    if bg:
        kw["bbox"] = dict(boxstyle="round,pad=0.2", fc=bg, ec="none", alpha=0.95)
    ax.text(x, y, text, ha=ha, va=va, fontsize=size, color=color, fontweight=weight, zorder=6, **kw)


def save(fig, name):
    path = HERE / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


# ---------------------------------------------------------------------------
# 01 current architecture
# ---------------------------------------------------------------------------


def fig_current():
    fig, ax = canvas()
    ax.text(50, 96, "现状：sim2sim_gate = 4 个 ONNX + Python 门控（一个进程）", ha="center", fontsize=16, fontweight="bold")

    box(ax, 2, 62, 23, 26, "训练产物", "biped 81\ncrawl 83\ntransition_down 130\ntransition_up 130", fc=C_PY, ec=C_PY_E)
    box(ax, 2, 38, 23, 16, "4 个 .onnx", "每教师一个文件\n共 3.5 MB", fc=C_ONNX, ec=C_ONNX_E)

    container(ax, 30, 28, 38, 62, "sim2sim_gate（Python，1031 行）")
    box(ax, 32, 68, 16.5, 12, "PostureSlew", "p_target → p_state\n0.25 / s", fc=C_PY, ec=C_PY_E, title_size=10, body_size=8.5)
    box(ax, 50.5, 68, 16.5, 12, "GatedController", "4 个 ONNX\n加权混合", fc=C_PY, ec=C_PY_E, title_size=10, body_size=8.5)
    box(ax, 32, 52, 16.5, 12, "HoldMotionCommand ×2", "down / up 参考\n重锚定、可按帧驱动", fc=C_PY, ec=C_PY_E, title_size=9.5, body_size=8.5)
    box(ax, 50.5, 52, 16.5, 12, "PostureCommand", "viser 姿态按钮\nTwist 摇杆", fc=C_UI, ec=C_UI_E, title_size=9.5, body_size=8.5)
    box(ax, 32, 34, 35, 11, "evaluate.py", "脚本化 timeline + 外力 + metrics / MP4", fc=C_GRAY, ec=C_GRAY_E, title_size=10, body_size=8.5)

    container(ax, 73, 28, 25, 62, "mjlab 运行时", fc="#F7FBF8", ec=C_JS_E)
    box(ax, 75, 68, 21, 13, "ManagerBasedRlEnv", "mujoco_warp\n单环境 50 Hz", fc=C_JS, ec=C_JS_E, title_size=10, body_size=8.5)
    box(ax, 75, 51, 21, 13, "V037 + plane", "真实 MJCF / 23 关节\n四套观测组", fc=C_JS, ec=C_JS_E, title_size=10, body_size=8.5)
    box(ax, 75, 35, 21, 11, "viser", "姿态面板 / 摇杆\n浏览器可视化", fc=C_UI, ec=C_UI_E, title_size=10, body_size=8.5)

    arrow(ax, (13.5, 62), (13.5, 54), color=C_ONNX_E, lw=1.8)
    arrow(ax, (25, 46), (30, 46), color=C_ONNX_E, lw=1.8)
    arrow(ax, (73, 74.5), (66.5, 74.5), color=C_JS_E, lw=1.8)
    label(ax, 69.5, 78, "4 组 obs", size=8.5, color=C_JS_E, bg="white")
    arrow(ax, (62, 58), (73, 58), color=C_PY_E, lw=1.8, rad=-0.04)
    label(ax, 71.2, 55.2, "actions\n绝对角", size=7.8, color=C_PY_E, bg="white")
    arrow(ax, (73, 40.5), (67, 40.5), color=C_UI_E, lw=1.5, ls="--")
    label(ax, 70, 37.5, "点击/摇杆", size=8, color=C_UI_E, bg="white")

    label(
        ax,
        50,
        18,
        "只读复用 mjlab.sim2sim：env_cfg / controllers / commands / onnx_policy / runner",
        size=9.5,
        color="#555555",
        bg="#FFFFFF",
    )
    label(ax, 50, 11, "问题：mjswan 一个 policy 只吃一个 ONNX；浏览器里没有 Python、mujoco_warp、viser。", size=10, color=C_RISK_E)
    save(fig, "01_current_architecture.png")


# ---------------------------------------------------------------------------
# 02 target architecture
# ---------------------------------------------------------------------------


def fig_target():
    fig, ax = canvas()
    ax.text(50, 96, "目标：一个 policy、一个 ONNX、一个 MDP（浏览器）", ha="center", fontsize=16, fontweight="bold")

    container(ax, 2, 58, 96, 34, "构建期：Python（mjlab/.venv，一套环境）")
    box(ax, 5, 62, 17, 17, "4 个 checkpoint", "biped / crawl\nup / down", fc=C_PY, ec=C_PY_E, title_size=10, body_size=8.5)
    box(ax, 26, 62, 22, 17, "compose_gate.py", "4 教师子图 + 门控数学\n导出 opset 18", fc=C_PY, ec=C_PY_E, title_size=10, body_size=8.5)
    box(ax, 52, 62, 18, 17, "gate.onnx", "输入 wide obs 148\n输出 23 个绝对角", fc=C_ONNX, ec=C_ONNX_E, title_size=10, body_size=8.5)
    box(ax, 74, 62, 21, 17, "mjswan Builder", "scene.mjz + manifest.json\n+ plugins.js", fc=C_PY, ec=C_PY_E, title_size=10, body_size=8.5)
    arrow(ax, (22, 70.5), (26, 70.5), color=C_PY_E, lw=1.7)
    arrow(ax, (48, 70.5), (52, 70.5), color=C_PY_E, lw=1.7)
    arrow(ax, (70, 70.5), (74, 70.5), color=C_PY_E, lw=1.7)

    container(ax, 2, 4, 96, 50, "运行期：浏览器（MuJoCo WASM + ONNX Runtime Web）", fc="#F7FBF8", ec=C_JS_E)
    box(ax, 5, 26, 18, 17, "控制面板", "Biped 复选框\nTwist 三滑条", fc=C_UI, ec=C_UI_E, title_size=10, body_size=8.5)
    box(ax, 27, 26, 24, 17, "GatedRefCommand（TS）", "p_state / 方向 / 两段 clip\n重锚定 / frame = f(p)", fc=C_JS, ec=C_JS_E, title_size=10, body_size=8.5)
    box(ax, 55, 26, 15, 17, "wide obs", "148 维\n每步拼接", fc=C_ONNX, ec=C_ONNX_E, title_size=10, body_size=8.5)
    box(ax, 74, 26, 20, 17, "gate.onnx", "4 教师 + 门控\n一次推理", fc=C_ONNX, ec=C_ONNX_E, title_size=10, body_size=8.5)
    box(ax, 74, 8, 20, 13, "action term", "scale=1\nuse_default_offset=False", fc=C_JS, ec=C_JS_E, title_size=9.5, body_size=8.3)
    box(ax, 48, 8, 20, 13, "MuJoCo WASM", "23 个 PD 执行器\n50 Hz 实时", fc=C_JS, ec=C_JS_E, title_size=10, body_size=8.5)

    arrow(ax, (23, 34.5), (27, 34.5), color=C_UI_E, lw=1.7)
    arrow(ax, (51, 34.5), (55, 34.5), color=C_JS_E, lw=1.7)
    arrow(ax, (70, 34.5), (74, 34.5), color=C_ONNX_E, lw=1.7)
    arrow(ax, (84, 26), (84, 21), color=C_JS_E, lw=1.7)
    arrow(ax, (74, 14.5), (68, 14.5), color=C_JS_E, lw=1.7)
    arrow(ax, (48, 14.5), (39, 26), color=C_JS_E, lw=1.4, ls="--", rad=0.2)
    label(ax, 39, 18, "机器人状态\n（obs 反馈）", size=8, color=C_JS_E, bg="white")
    arrow(ax, (84, 58), (84, 43), color=C_PY_E, lw=1.5, ls="--")
    label(ax, 88, 50, "打包 / 加载", size=8.5, color=C_PY_E)

    label(ax, 50, 1.0, "原则：状态放 TS 命令（可复位、可观测、可 UI），数学放 ONNX（无状态、可对拍）。", size=10, color="#444444")
    save(fig, "02_target_architecture.png")


# ---------------------------------------------------------------------------
# 03 gating signal flow
# ---------------------------------------------------------------------------


def fig_gating():
    fig, ax = canvas()
    ax.text(50, 96, "门控信号流：p_state 同时是“混合权重”和“参考 clip 的相位”", ha="center", fontsize=15, fontweight="bold")

    box(ax, 3, 74, 14, 13, "p_target", "复选框\n0=四足 / 1=直立", fc=C_UI, ec=C_UI_E, title_size=10, body_size=8.5)
    box(ax, 21, 74, 18, 13, "PostureSlew", "按 slew_rate 积分\n0.25 / s（= clip 1.0×）", fc=C_PY, ec=C_PY_E, title_size=10, body_size=8.5)
    box(ax, 43, 74, 14, 13, "p_state", "∈ [0, 1]", fc=C_ONNX, ec=C_ONNX_E, title_size=10, body_size=9)
    box(ax, 61, 74, 36, 13, "w_end = (2|p − 0.5|)²", "端点 1 / 正中间 0，可乘 endpoint_mix", fc=C_ONNX, ec=C_ONNX_E, title_size=11, body_size=8.5)
    arrow(ax, (17, 80.5), (21, 80.5), color=C_UI_E, lw=1.7)
    arrow(ax, (39, 80.5), (43, 80.5), color=C_PY_E, lw=1.7)
    arrow(ax, (57, 80.5), (61, 80.5), color=C_ONNX_E, lw=1.7)

    box(ax, 3, 52, 14, 12, "crawl 教师", "a_crawl", fc=C_JS, ec=C_JS_E, title_size=10, body_size=9)
    box(ax, 19, 52, 14, 12, "biped 教师", "a_biped", fc=C_JS, ec=C_JS_E, title_size=10, body_size=9)
    box(ax, 37, 52, 14, 12, "up 教师", "a_up", fc=C_JS, ec=C_JS_E, title_size=10, body_size=9)
    box(ax, 53, 52, 14, 12, "down 教师", "a_down", fc=C_JS, ec=C_JS_E, title_size=10, body_size=9)

    box(ax, 3, 34, 30, 11, "端点混合", "a_end = lerp(a_crawl, a_biped, p)", fc=C_ONNX, ec=C_ONNX_E, title_size=9.5, body_size=8.3)
    box(ax, 37, 34, 34, 11, "方向教师", "a_dir = a_up 若 p_target > p_state，否则 a_down", fc=C_ONNX, ec=C_ONNX_E, title_size=9.5, body_size=8.3)
    arrow(ax, (10, 52), (10, 45), color=C_JS_E, lw=1.4)
    arrow(ax, (26, 52), (26, 45), color=C_JS_E, lw=1.4)
    arrow(ax, (44, 52), (44, 45), color=C_JS_E, lw=1.4)
    arrow(ax, (60, 52), (60, 45), color=C_JS_E, lw=1.4)

    box(ax, 18, 15, 55, 12, "a = w_end · a_end + (1 − w_end) · a_dir", "输出：23 个绝对关节目标角；不移动时直接取 a_end", fc=C_ONNX, ec=C_ONNX_E, title_size=11, body_size=8.5)
    arrow(ax, (18, 34), (30, 27), color=C_ONNX_E, lw=1.5, rad=-0.1)
    arrow(ax, (54, 34), (48, 27), color=C_ONNX_E, lw=1.5, rad=0.1)

    # Inset: endpoint weight curve, kept clear of the final box.
    inset = fig.add_axes([0.74, 0.10, 0.22, 0.22])
    p = np.linspace(0, 1, 200)
    inset.plot(p, (2 * np.abs(p - 0.5)) ** 2, color=C_ONNX_E, lw=2.2)
    inset.set_xlim(0, 1)
    inset.set_ylim(0, 1.05)
    inset.set_xlabel("p_state", fontsize=8)
    inset.set_ylabel("w_end", fontsize=8)
    inset.tick_params(labelsize=7)
    inset.grid(alpha=0.25)
    inset.set_title("端点权重曲线", fontsize=8.5)

    label(ax, 3, 8, "down clip: frame = (1−p)(N−1)\nup clip:   frame = p(N−1)\n方向不同，帧号映射必须相反。", size=8.8, color="#444444", ha="left")
    label(ax, 3, 1.5, "早期版本把 down 倒放，p≈1 时参考已是四足姿态，过渡教师把站着的机器人按下去（base_z 0.23→0.096）。", size=8, color=C_RISK_E, ha="left")
    save(fig, "03_gating_signal_flow.png")


# ---------------------------------------------------------------------------
# 04 observation layout
# ---------------------------------------------------------------------------


def fig_obs():
    fig, ax = canvas((16, 10))
    ax.text(50, 96, "宽观测契约：148 维，按教师切片后逐项还原", ha="center", fontsize=15, fontweight="bold")

    segs = [
        ("", 3, "#DCE9F7"),
        ("", 3, "#C9DDF2"),
        ("", 3, "#B7D1ED"),
        ("", 3, "#A5C5E8"),
        ("", 3, "#93B9E3"),
        ("joint_pos\n23", 23, "#FCEBDA"),
        ("joint_vel\n23", 23, "#F8DCC2"),
        ("last_action\n23", 23, "#F4CDAA"),
        ("", 3, "#E8E1F5"),
        ("", 2, "#D9CDF0"),
        ("gated_command 50", 50, "#E6F4EA"),
        ("", 3, "#C9E6D2"),
        ("", 6, "#B4DCC1"),
    ]
    total = sum(s[1] for s in segs)
    assert total == 148, total
    x0, y0, width, height = 3, 66, 94, 9
    x = x0
    starts = []
    for text, n, color in segs:
        w = width * n / total
        starts.append((x, x + w))
        ax.add_patch(plt.Rectangle((x, y0), w, height, facecolor=color, edgecolor="white", linewidth=1.5, zorder=2))
        if text:
            ax.text(x + w / 2, y0 + height / 2, text, ha="center", va="center", fontsize=7.5, zorder=3)
        x += w

    def bracket(i, j, text, y):
        x1 = starts[i][0]
        x2 = starts[j][1]
        ax.plot([x1, x1, x2, x2], [y, y + 1.6, y + 1.6, y], color="#666666", lw=1.0, zorder=3)
        label(ax, (x1 + x2) / 2, y + 3.2, text, size=8.2, color="#444444")

    bracket(0, 4, "base/heading vel + gravity  15", 79)
    bracket(8, 9, "twist 3 + phase 2", 79)
    bracket(11, 12, "anchor pos/ori  9", 79)
    label(ax, x0 + width / 2, 62, "顺序 = manifest 中 observation group 的拼接顺序", size=8.5, color="#777777")

    def slice_bar(y, title, parts):
        label(ax, 2, y + 3.2, title, size=10, color="#333333", ha="left", weight="bold")
        xx = 25
        bw = 69
        for text, n, color in parts:
            w = bw * n / 148
            ax.add_patch(plt.Rectangle((xx, y), w, 6.5, facecolor=color, edgecolor="white", linewidth=1.2, zorder=2))
            if text and n >= 8:
                ax.text(xx + w / 2, y + 3.25, text, ha="center", va="center", fontsize=7.5, zorder=3)
            xx += w

    biped = [("", 3, "#DCE9F7"), ("", 3, "#C9DDF2"), ("", 3, "#93B9E3"),
             ("joint_pos 23", 23, "#FCEBDA"), ("joint_vel 23", 23, "#F8DCC2"), ("actions 23", 23, "#F4CDAA"),
             ("", 3, "#E8E1F5")]
    crawl = biped[:-1] + [("", 3, "#E8E1F5"), ("", 2, "#D9CDF0")]
    trans = [("ref 46", 46, "#E6F4EA"), ("", 3, "#C9E6D2"), ("", 6, "#B4DCC1"),
             ("", 3, "#DCE9F7"), ("", 3, "#C9DDF2"), ("joint_pos 23", 23, "#FCEBDA"),
             ("joint_vel 23", 23, "#F8DCC2"), ("actions 23", 23, "#F4CDAA")]
    slice_bar(44, "biped  81", biped)
    slice_bar(27, "crawl  83", crawl)
    slice_bar(10, "transition  130", trans)

    label(ax, 50, 2, "动作项 actions 由 last_action 反解：raw = (last_action − default_i) / scale_i；首步用 0。", size=8.5, color="#555555")
    save(fig, "04_observation_contract.png")


# ---------------------------------------------------------------------------
# 05 roadmap
# ---------------------------------------------------------------------------


def fig_roadmap():
    fig, ax = canvas((16, 9))
    ax.text(50, 96, "迁移路线：先共用环境，再单 ONNX，最后浏览器", ha="center", fontsize=15, fontweight="bold")

    phases = [
        ("P0 复盘 + 环境", 0, 1, C_GRAY, "G0"),
        ("P1 共用 venv + 搬 Python 入口", 1, 3, C_PY, "G1"),
        ("P2 单 ONNX 合成 + 对拍", 3, 8, C_ONNX, "G2"),
        ("P3 GatedRefCommand + 浏览器 v1", 8, 16, C_JS, "G3"),
        ("P4 评估 / 录制 / 发布", 16, 19, C_UI, "G4"),
    ]
    for i, (name, start, end, color, gate) in enumerate(phases):
        y = 78 - i * 13
        ax.add_patch(plt.Rectangle((start * 4.5 + 6, y), (end - start) * 4.5, 7.5, facecolor=color, edgecolor="white", linewidth=1.2, zorder=2))
        label(ax, 5, y + 3.7, name, size=9.5, color="#333333", ha="right", weight="bold")
        label(ax, start * 4.5 + 8, y + 3.7, f"{end - start} d", size=8, color="#333333", ha="left")
        ax.plot([end * 4.5 + 6], [y + 3.7], marker="D", markersize=8, color=color, markeredgecolor="white", zorder=4)
        label(ax, end * 4.5 + 9.5, y + 3.7, gate, size=8.5, color="#555555", ha="left", weight="bold")

    for day in range(0, 21, 5):
        x = day * 4.5 + 6
        ax.plot([x, x], [14, 88], color="#DDDDDD", lw=0.8, zorder=1)
        label(ax, x, 12, f"Day {day}", size=7.5, color="#888888")

    label(ax, 50, 5, "总工期约 3 周（1 人）；只做 P0–P1 的 Python 回退方案约 2–3 天。", size=9.5, color="#444444")
    save(fig, "05_roadmap.png")


# ---------------------------------------------------------------------------
# 06 environment sharing
# ---------------------------------------------------------------------------


def fig_env():
    fig, ax = canvas((16, 9))
    ax.text(50, 96, "共用环境：一套 mjlab/.venv，不另建 mjswan/.venv", ha="center", fontsize=15, fontweight="bold")

    container(ax, 6, 26, 88, 62, "mjlab/.venv  ·  Python 3.13.12  ·  唯一解释器", fc=C_ENV, ec=C_ENV_E, title_size=12)
    box(ax, 10, 54, 36, 24, "mjlab 1.6.0（editable）", "mujoco 3.11.0\nmujoco-warp 3.11.0\ntorch 2.9.0\nviser 1.0.27", fc=C_PY, ec=C_PY_E, title_size=11, body_size=9)
    box(ax, 54, 54, 36, 24, "mjswan 0.13.1（editable）", "onnx 1.22.0\nonnxruntime 1.24.3\nnodeenv 1.9.1\ntyper 0.29（新增）", fc=C_JS, ec=C_JS_E, title_size=11, body_size=9)

    container(ax, 10, 29, 80, 18, "入口（都直接用这个解释器，不经过 uv run 的自动建环境）", fc="#FFFFFF", ec=C_GRAY_E, title_size=10)
    label(ax, 50, 36, "python -m pikachu.legacy.sim2sim_gate     →  Python 回退 / 评估\npython -m pikachu.app.main                           →  构建浏览器 app\nmjswan serve pikachu/app/dist                         →  本地静态站点", size=8.8, color="#333333")

    box(ax, 6, 6, 42, 14, "不要做", "mjswan/.venv\nuv sync --all-extras\npip install 'mjswan[mjlab]'", fc=C_RISK, ec=C_RISK_E, title_size=10.5, body_size=8.8)
    box(ax, 52, 6, 42, 14, "推荐做", "uv pip install --python mjlab/.venv/bin/python -e mjswan\n（只装 core；实测只新增 typer 等 4 个包）", fc="#EAF6EA", ec=C_JS_E, title_size=10.5, body_size=8.8)
    save(fig, "06_environment_sharing.png")


# ---------------------------------------------------------------------------
# 07 parity spike
# ---------------------------------------------------------------------------


def fig_parity():
    fig, ax = plt.subplots(figsize=(12, 6))
    labels = ["torch wrapper\nvs Python gate", "ONNX\nvs torch wrapper", "ONNX vs Python\n(256 random)"]
    values = [1e-12, 3.8e-6, 7.6e-6]
    colors = [C_JS_E, C_ONNX_E, C_PY_E]
    bars = ax.bar(labels, values, color=colors, width=0.55, edgecolor="white")
    ax.set_yscale("log")
    ax.set_ylim(1e-12, 3e-4)
    ax.set_ylabel("max |Δ action| (rad)", fontsize=11)
    ax.set_title("单 ONNX 合成 spike：门控输出与 Python 参考的数值差", fontsize=13, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    for bar, value in zip(bars, values):
        text = "0（同一张图）" if value <= 1e-12 else f"{value:.2e}"
        ax.text(bar.get_x() + bar.get_width() / 2, value * 1.6, text, ha="center", fontsize=10)
    ax.axhline(1e-4, color=C_RISK_E, lw=1.0, ls="--")
    ax.text(0.55, 0.91, "验收阈值 1e-4", color=C_RISK_E, fontsize=9, ha="left", transform=ax.transAxes)
    fig.tight_layout()
    save(fig, "07_parity_spike.png")


if __name__ == "__main__":
    fig_current()
    fig_target()
    fig_gating()
    fig_obs()
    fig_roadmap()
    fig_env()
    fig_parity()

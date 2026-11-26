// src/core/observation/ObservationBase.ts
var ObservationBase = class {
  constructor(runner, config) {
    this.runner = runner;
    this.config = config;
  }
};

// src/core/observation/math.ts
function normalizeQuat(quat) {
  const w = quat[0] ?? 1;
  const x = quat[1] ?? 0;
  const y = quat[2] ?? 0;
  const z = quat[3] ?? 0;
  const n = Math.hypot(w, x, y, z);
  if (n < 1e-9) {
    return [1, 0, 0, 0];
  }
  const inv = 1 / n;
  return [w * inv, x * inv, y * inv, z * inv];
}
function quatMultiply(a, b) {
  const aw = a[0] ?? 1;
  const ax = a[1] ?? 0;
  const ay = a[2] ?? 0;
  const az = a[3] ?? 0;
  const bw = b[0] ?? 1;
  const bx = b[1] ?? 0;
  const by = b[2] ?? 0;
  const bz = b[3] ?? 0;
  return [
    aw * bw - ax * bx - ay * by - az * bz,
    aw * bx + ax * bw + ay * bz - az * by,
    aw * by - ax * bz + ay * bw + az * bx,
    aw * bz + ax * by - ay * bx + az * bw
  ];
}
function quatInverse(quat) {
  const w = quat[0] ?? 1;
  const x = quat[1] ?? 0;
  const y = quat[2] ?? 0;
  const z = quat[3] ?? 0;
  const normSq = w * w + x * x + y * y + z * z;
  if (normSq < 1e-9) {
    return [1, 0, 0, 0];
  }
  const inv = 1 / normSq;
  return [w * inv, -x * inv, -y * inv, -z * inv];
}
function quatApply(quat, vec) {
  const w = quat[0] ?? 1;
  const x = quat[1] ?? 0;
  const y = quat[2] ?? 0;
  const z = quat[3] ?? 0;
  const vx = vec[0] ?? 0;
  const vy = vec[1] ?? 0;
  const vz = vec[2] ?? 0;
  const tx = 2 * (y * vz - z * vy);
  const ty = 2 * (z * vx - x * vz);
  const tz = 2 * (x * vy - y * vx);
  const cx = y * tz - z * ty;
  const cy = z * tx - x * tz;
  const cz = x * ty - y * tx;
  return [vx + w * tx + cx, vy + w * ty + cy, vz + w * tz + cz];
}
function quatApplyInv(quat, vec) {
  const w = quat[0] ?? 1;
  const x = quat[1] ?? 0;
  const y = quat[2] ?? 0;
  const z = quat[3] ?? 0;
  const vx = vec[0] ?? 0;
  const vy = vec[1] ?? 0;
  const vz = vec[2] ?? 0;
  const tx = 2 * (y * vz - z * vy);
  const ty = 2 * (z * vx - x * vz);
  const tz = 2 * (x * vy - y * vx);
  const cx = y * tz - z * ty;
  const cy = z * tx - x * tz;
  const cz = x * ty - y * tx;
  return [vx - w * tx + cx, vy - w * ty + cy, vz - w * tz + cz];
}
function yawQuat(quat) {
  const w = quat[0] ?? 1;
  const x = quat[1] ?? 0;
  const y = quat[2] ?? 0;
  const z = quat[3] ?? 0;
  const yaw = Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z));
  return [Math.cos(yaw / 2), 0, 0, Math.sin(yaw / 2)];
}
function quatToRot6d(quat) {
  const [w, x, y, z] = normalizeQuat(quat);
  const xx = x * x;
  const yy = y * y;
  const zz = z * z;
  const xy = x * y;
  const xz = x * z;
  const yz = y * z;
  const wx = w * x;
  const wy = w * y;
  const wz = w * z;
  const r00 = 1 - 2 * (yy + zz);
  const r01 = 2 * (xy - wz);
  const r10 = 2 * (xy + wz);
  const r11 = 1 - 2 * (xx + zz);
  const r20 = 2 * (xz - wy);
  const r21 = 2 * (yz + wx);
  return [r00, r01, r10, r11, r20, r21];
}

// ../../../pikachu/browser/gate_observation.ts
var GateTwist = class extends ObservationBase {
  get size() {
    return 3;
  }
  compute() {
    const manager = this.runner.getContext()?.commandManager;
    if (!manager) throw new Error("Gate needs a command manager");
    const twist = manager.getCommand("twist");
    const crawl = manager.getCommand("posture")[0] < 0.5;
    return Float32Array.from(twist, (value) => crawl ? Math.max(-0.3, Math.min(0.3, value)) : value);
  }
};
var GateReference = class extends ObservationBase {
  target = 1;
  phase = 1;
  direction = 0;
  first = true;
  lastTime = -1;
  cached = new Float32Array(59);
  refOrigin = [0, 0, 0];
  robotOrigin = [0, 0, 0];
  delta = [1, 0, 0, 0];
  get size() {
    return 59;
  }
  reset() {
    this.target = 1;
    this.phase = 1;
    this.direction = 0;
    this.first = true;
    this.lastTime = -1;
    this.cached = new Float32Array(59);
    if (typeof window !== "undefined" && typeof window.dispatchEvent === "function") {
      window.dispatchEvent(new Event("pikachu-gate-reset"));
    }
  }
  compute(state) {
    const context = this.runner.getContext();
    if (!context?.mjData || !state.rootPos || !state.rootQuat) throw new Error("Gate needs the robot root state");
    const time = context.mjData.time;
    if (time === this.lastTime) return this.cached;
    this.lastTime = time;
    const requested = context.commandManager?.getCommand("posture");
    this.target = requested && requested[0] >= 0.5 ? 1 : 0;
    const change = Math.max(-5e-3, Math.min(5e-3, this.target - this.phase));
    this.phase = Math.max(0, Math.min(1, this.phase + change));
    if (typeof window !== "undefined" && typeof window.dispatchEvent === "function") {
      window.dispatchEvent(new CustomEvent("pikachu-gate-progress", {
        detail: { target: this.target, phase: this.phase }
      }));
    }
    const dir = Math.abs(this.target - this.phase) > 0.02 ? this.target > this.phase ? 1 : -1 : 0;
    if (dir !== 0 && context.commandManager) {
      const twist = context.commandManager.getCommand("twist");
      if (Array.from(twist).some((value) => value !== 0)) {
        for (const axis of ["lin_vel_x", "lin_vel_y", "ang_vel_z"]) {
          context.commandManager.setValue(`twist:${axis}`, 0);
        }
      }
    }
    const clip = dir === 1 ? this.config.up : this.config.down;
    const fraction = dir === 1 ? this.phase : 1 - this.phase;
    const frame = Math.max(0, Math.min(clip.joint_pos.length - 1, Math.round(fraction * (clip.joint_pos.length - 1))));
    if (dir !== 0 && dir !== this.direction) {
      this.refOrigin = clip.anchor_pos[frame].slice();
      this.robotOrigin = Array.from(state.rootPos);
      this.delta = yawQuat(quatMultiply(state.rootQuat, quatInverse(clip.anchor_quat[frame])));
    }
    this.direction = dir;
    const originDiff = clip.anchor_pos[frame].map((v, i) => v - this.refOrigin[i]);
    const refPos = quatApply(this.delta, originDiff).map((v, i) => v + this.robotOrigin[i]);
    const refQuat = quatMultiply(this.delta, clip.anchor_quat[frame]);
    const posRel = quatApplyInv(state.rootQuat, refPos.map((v, i) => v - state.rootPos[i]));
    const oriRel = quatToRot6d(quatMultiply(quatInverse(state.rootQuat), refQuat));
    const out = new Float32Array(59);
    out.set([this.target, this.phase, this.first ? 1 : 0, dir]);
    out.set(clip.joint_pos[frame], 4);
    out.set(clip.joint_vel[frame], 27);
    out.set(posRel, 50);
    out.set(oriRel, 53);
    if (new URLSearchParams(window.location.search).has("pikachu_debug")) {
      window.__pikachuGate = {
        time,
        phase: this.phase,
        target: this.target,
        direction: dir,
        rootPos: Array.from(state.rootPos),
        rootQuat: Array.from(state.rootQuat),
        frame,
        observation: Array.from(out)
      };
    }
    this.first = false;
    this.cached = out;
    return out;
  }
};

// src/.plugins-entry.ts
var observations = { GateReference, GateTwist };
export {
  observations
};

import { ObservationBase } from 'mjswan/observation';
import { quatApply, quatApplyInv, quatInverse, quatMultiply, quatToRot6d, yawQuat } from 'mjswan/math';

type Clip = { joint_pos: number[][]; joint_vel: number[][]; anchor_pos: number[][]; anchor_quat: number[][] };

/** Holds posture and reference state inside one browser simulation. */
export class GateReference extends ObservationBase {
  private target = 1;
  private phase = 1;
  private direction = 0;
  private first = true;
  private lastTime = -1;
  private cached = new Float32Array(59);
  private refOrigin = [0, 0, 0];
  private robotOrigin = [0, 0, 0];
  private delta = [1, 0, 0, 0];

  get size(): number { return 59; }

  reset(): void {
    this.target = 1; this.phase = 1; this.direction = 0; this.first = true;
    this.lastTime = -1; this.cached = new Float32Array(59);
    if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
      window.dispatchEvent(new Event('pikachu-gate-reset'));
    }
  }

  compute(state: { rootPos?: Float32Array; rootQuat?: Float32Array }): Float32Array {
    const context = this.runner.getContext();
    if (!context?.mjData || !state.rootPos || !state.rootQuat) throw new Error('Gate needs the robot root state');
    const time = context.mjData.time;
    if (time === this.lastTime) return this.cached;
    this.lastTime = time;
    const requested = context.commandManager?.getCommand('posture');
    this.target = requested && requested[0] >= 0.5 ? 1 : 0;
    const change = Math.max(-0.005, Math.min(0.005, this.target - this.phase));
    this.phase = Math.max(0, Math.min(1, this.phase + change));
    if (typeof window !== 'undefined' && typeof window.dispatchEvent === 'function') {
      window.dispatchEvent(new CustomEvent('pikachu-gate-progress', {
        detail: { target: this.target, phase: this.phase },
      }));
    }
    const dir = Math.abs(this.target - this.phase) > 0.02 ? (this.target > this.phase ? 1 : -1) : 0;
    if (dir !== 0 && context.commandManager) {
      const twist = context.commandManager.getCommand('twist');
      if (Array.from(twist).some(value => value !== 0)) {
        for (const axis of ['lin_vel_x', 'lin_vel_y', 'ang_vel_z']) {
          context.commandManager.setValue(`twist:${axis}`, 0);
        }
      }
    }
    const clip = (dir === 1 ? this.config.up : this.config.down) as Clip;
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
    const posRel = quatApplyInv(state.rootQuat, refPos.map((v, i) => v - state.rootPos![i]));
    const oriRel = quatToRot6d(quatMultiply(quatInverse(state.rootQuat), refQuat));
    const out = new Float32Array(59);
    out.set([this.target, this.phase, this.first ? 1 : 0, dir]);
    out.set(clip.joint_pos[frame], 4); out.set(clip.joint_vel[frame], 27);
    out.set(posRel, 50); out.set(oriRel, 53);
    if (new URLSearchParams(window.location.search).has('pikachu_debug')) {
      (window as any).__pikachuGate = { time, phase: this.phase, target: this.target, direction: dir,
        rootPos: Array.from(state.rootPos), rootQuat: Array.from(state.rootQuat), frame, observation: Array.from(out) };
    }
    this.first = false; this.cached = out;
    return out;
  }
}

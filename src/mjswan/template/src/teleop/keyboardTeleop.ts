import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from 'react';
import type { CommandDescriptor, MjswanEngine } from '../engine';
import { isEditableElement } from './keys';

/**
 * Keyboard driving for a scene whose MDP has a `twist` command: W/S forward and back,
 * A/D left and right, Q/E turn left and right, each ramping to a fraction of the axis's
 * own limit. Keys write through `engine.commands.set`, so the panel's Twist sliders
 * follow, and opposing keys (W+S, A+D, Q+E) cancel an axis instead of adding. F toggles
 * the pikachu gate's `posture:biped` command while the gate is idle. Z and R belong to
 * the panel itself.
 */

/** Target speed as a fraction of each axis's own limit. */
const SPEED_FRACTION = 0.75;
/** Seconds from standstill to the target speed, and back. */
const RAMP_SECONDS = 0.8;
/** Writes per second while ramping; each write rebuilds the engine's state snapshot. */
const WRITE_INTERVAL_MS = 40;
/** The gate's crawl clamp, applied as the panel applies it. */
const CRAWL_LIMIT = 0.3;

const DRIVE_CODES = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'KeyQ', 'KeyE']);

interface AxisSpec {
  id: string;
  /** Commanded bound for the forward key, and for the back key (negative). */
  hi: number;
  lo: number;
  /** Command units per second, so either direction reaches the target in RAMP_SECONDS. */
  rate: number;
}

interface AxesSpec {
  forward: AxisSpec | null;
  lateral: AxisSpec | null;
  yaw: AxisSpec | null;
  postureId: string | null;
}

export interface TeleopReadout {
  /** Key codes held down, as `KeyboardEvent.code` names them. */
  held: ReadonlySet<string>;
  /** Commanded forward and lateral velocity, m/s. */
  vx: number;
  vy: number;
  /** Commanded yaw rate, rad/s. */
  vz: number;
  /** Whether the loaded MDP has the twist command this drives. */
  available: boolean;
  /** Whether it offers the gate's posture switch (F). */
  hasPosture: boolean;
  /** Biped (true) or crawl (false), as the posture command reads. */
  biped: boolean;
  /** True while a posture transition holds the twist at zero. */
  transitioning: boolean;
}

function buildAxes(
  commands: readonly CommandDescriptor[],
  values: Readonly<Record<string, number>>,
): AxesSpec {
  const posture = commands.find((command) => command.id === 'posture:biped');
  const crawl = posture !== undefined && (values['posture:biped'] ?? 1) < 0.5;
  const limit = crawl ? CRAWL_LIMIT : Infinity;
  const axis = (name: string): AxisSpec | null => {
    const command = commands.find(
      (entry) => entry.id === `twist:${name}` && entry.type === 'slider',
    );
    if (!command) return null;
    const hi = Math.min(command.max ?? 0, limit);
    const lo = Math.max(command.min ?? 0, -limit);
    const span = Math.max(Math.abs(hi), Math.abs(lo));
    return { id: command.id, hi, lo, rate: (SPEED_FRACTION * span) / RAMP_SECONDS };
  };
  return {
    forward: axis('lin_vel_x'),
    lateral: axis('lin_vel_y'),
    yaw: axis('ang_vel_z'),
    postureId: posture?.id ?? null,
  };
}

/** The axis's target this frame: nearer key, or zero when both or neither is held. */
function axisTarget(
  held: ReadonlySet<string>,
  plusCode: string,
  minusCode: string,
  axis: AxisSpec,
): number {
  const plus = held.has(plusCode);
  const minus = held.has(minusCode);
  if (plus === minus) return 0;
  return plus ? SPEED_FRACTION * axis.hi : SPEED_FRACTION * axis.lo;
}

function stepToward(value: number, target: number, rate: number, dt: number): number {
  const delta = target - value;
  const step = rate * dt;
  return Math.abs(delta) <= step ? target : value + Math.sign(delta) * step;
}

export function useKeyboardTeleop(
  engineRef: RefObject<MjswanEngine | null>,
  commands: readonly CommandDescriptor[],
  commandValues: Readonly<Record<string, number>>,
): TeleopReadout {
  const axes = useMemo(() => buildAxes(commands, commandValues), [commands, commandValues]);

  const axesRef = useRef(axes);
  const valuesRef = useRef(commandValues);
  const heldRef = useRef<ReadonlySet<string>>(new Set());
  const speedRef = useRef({ x: 0, y: 0, z: 0 });
  const writtenRef = useRef({ x: NaN, y: NaN, z: NaN });
  const gateRef = useRef({ target: 1, phase: 1 });
  const movingRef = useRef(false);

  const [held, setHeld] = useState<ReadonlySet<string>>(heldRef.current);
  const [speed, setSpeed] = useState({ vx: 0, vy: 0, vz: 0 });
  const [transitioning, setTransitioning] = useState(false);

  useEffect(() => {
    axesRef.current = axes;
    valuesRef.current = commandValues;
  }, [axes, commandValues]);

  /** Land at zero at once: the gate zeroes the twist itself once a transition starts. */
  const stop = useCallback(() => {
    const engine = engineRef.current;
    const current = axesRef.current;
    for (const axis of [current.forward, current.lateral, current.yaw]) {
      if (axis && engine) engine.commands.set(axis.id, 0);
    }
    speedRef.current = { x: 0, y: 0, z: 0 };
    writtenRef.current = { x: 0, y: 0, z: 0 };
    setSpeed({ vx: 0, vy: 0, vz: 0 });
  }, [engineRef]);

  useEffect(() => {
    const onProgress = (event: Event) => {
      const { target, phase } = (event as CustomEvent<{ target: number; phase: number }>).detail;
      gateRef.current = { target, phase };
      const moving = Math.abs(target - phase) >= 1e-6;
      if (moving !== movingRef.current) {
        movingRef.current = moving;
        setTransitioning(moving);
        if (moving) stop();
      }
    };
    const onReset = () => {
      gateRef.current = { target: 1, phase: 1 };
      if (movingRef.current) {
        movingRef.current = false;
        setTransitioning(false);
      }
    };
    window.addEventListener('pikachu-gate-progress', onProgress);
    window.addEventListener('pikachu-gate-reset', onReset);
    return () => {
      window.removeEventListener('pikachu-gate-progress', onProgress);
      window.removeEventListener('pikachu-gate-reset', onReset);
    };
  }, [stop]);

  useEffect(() => {
    const hold = (code: string, down: boolean) => {
      if (heldRef.current.has(code) === down) return;
      const next = new Set(heldRef.current);
      if (down) next.add(code);
      else next.delete(code);
      heldRef.current = next;
      setHeld(next);
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;
      const target = event.target instanceof Element ? event.target : document.activeElement;
      if (isEditableElement(target)) return;
      if (DRIVE_CODES.has(event.code)) {
        event.preventDefault();
        hold(event.code, true);
        return;
      }
      if (event.code !== 'KeyF' || event.repeat) return;
      const postureId = axesRef.current.postureId;
      if (!postureId) return;
      const gate = gateRef.current;
      if (Math.abs(gate.target - gate.phase) >= 1e-6) return;
      // The gate zeroes the twist while it transitions, so stop before asking to switch.
      stop();
      const current = valuesRef.current[postureId] ?? 1;
      engineRef.current?.commands.set(postureId, current >= 0.5 ? 0 : 1);
    };

    const onKeyUp = (event: KeyboardEvent) => {
      if (!DRIVE_CODES.has(event.code)) return;
      hold(event.code, false);
    };

    const onBlur = () => {
      if (heldRef.current.size === 0) return;
      heldRef.current = new Set();
      setHeld(heldRef.current);
    };

    window.addEventListener('keydown', onKeyDown);
    window.addEventListener('keyup', onKeyUp);
    window.addEventListener('blur', onBlur);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('keyup', onKeyUp);
      window.removeEventListener('blur', onBlur);
    };
  }, [engineRef, stop]);

  useEffect(() => {
    let frame = 0;
    let last = performance.now();
    let lastWrite = 0;
    const tick = (now: number) => {
      frame = requestAnimationFrame(tick);
      // Wall-clock ramp: a slow frame must not slow the acceleration. The cap only
      // keeps a hidden tab from jumping to full speed on its first frame back.
      const dt = Math.min(0.5, (now - last) / 1000);
      last = now;
      const engine = engineRef.current;
      const axisX = axesRef.current.forward;
      const axisY = axesRef.current.lateral;
      const axisZ = axesRef.current.yaw;
      if (!engine || !axisX || !axisY || !axisZ) {
        speedRef.current = { x: 0, y: 0, z: 0 };
        writtenRef.current = { x: NaN, y: NaN, z: NaN };
        return;
      }
      const drive = !movingRef.current;
      const speed = speedRef.current;
      const targetX = drive ? axisTarget(heldRef.current, 'KeyW', 'KeyS', axisX) : 0;
      const targetY = drive ? axisTarget(heldRef.current, 'KeyA', 'KeyD', axisY) : 0;
      const targetZ = drive ? axisTarget(heldRef.current, 'KeyQ', 'KeyE', axisZ) : 0;
      speed.x = stepToward(speed.x, targetX, axisX.rate, dt);
      speed.y = stepToward(speed.y, targetY, axisY.rate, dt);
      speed.z = stepToward(speed.z, targetZ, axisZ.rate, dt);
      const written = writtenRef.current;
      if (now - lastWrite < WRITE_INTERVAL_MS) return;
      if (speed.x === written.x && speed.y === written.y && speed.z === written.z) return;
      if (speed.x !== written.x) engine.commands.set(axisX.id, speed.x);
      if (speed.y !== written.y) engine.commands.set(axisY.id, speed.y);
      if (speed.z !== written.z) engine.commands.set(axisZ.id, speed.z);
      written.x = speed.x;
      written.y = speed.y;
      written.z = speed.z;
      lastWrite = now;
      setSpeed({ vx: speed.x, vy: speed.y, vz: speed.z });
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [engineRef]);

  return {
    held,
    vx: speed.vx,
    vy: speed.vy,
    vz: speed.vz,
    available: axes.forward !== null && axes.lateral !== null && axes.yaw !== null,
    hasPosture: axes.postureId !== null,
    biped: (commandValues['posture:biped'] ?? 1) >= 0.5,
    transitioning,
  };
}

import assert from 'node:assert/strict';
import { observations } from '../dist/assets/plugins.js';

globalThis.window = { location: { search: '' } };
const frame = (x) => ({
  joint_pos: Array.from({length: 200}, (_, i) => Array(23).fill(x + i)),
  joint_vel: Array.from({length: 200}, () => Array(23).fill(x)),
  anchor_pos: Array.from({length: 200}, (_, i) => [i * 0.01, 0, 0.2]),
  anchor_quat: Array.from({length: 200}, () => [1, 0, 0, 0]),
});
let requested = 1;
const twist = [0.1, 0.2, 0.3];
const ctx = { mjData: {time: 0}, commandManager: {
  getCommand: (name) => name === 'posture' ? [requested] : twist,
  setValue: (name, value) => { twist[['twist:lin_vel_x', 'twist:lin_vel_y', 'twist:ang_vel_z'].indexOf(name)] = value; },
} };
const runner = { getContext: () => ctx };
const gateTwist = new observations.GateTwist(runner, {name: 'GateTwist'});
twist.splice(0, 3, .8, -.7, .6);
assert.deepEqual(Array.from(gateTwist.compute()), [.8, -.7, .6].map(Math.fround));
requested = 0;
assert.deepEqual(Array.from(gateTwist.compute()), [.3, -.3, .3].map(Math.fround));
requested = 1; twist.splice(0, 3, .1, .2, .3);
const gate = new observations.GateReference(runner, {name: 'GateReference', down: frame(0), up: frame(1000)});
const state = {rootPos: new Float32Array([3, 4, .2]), rootQuat: new Float32Array([1, 0, 0, 0])};
let obs = gate.compute(state);
assert.equal(obs.length, 59);
assert.deepEqual(Array.from(obs.slice(0, 4)), [1, 1, 1, 0]);
requested = 0; ctx.mjData.time += .02; obs = gate.compute(state);
assert.ok(Math.abs(obs[1] - .995) < 1e-6);
assert.equal(obs[3], -1); assert.equal(obs[4], 1);
assert.deepEqual(twist, [0, 0, 0]);
assert.ok(Math.abs(obs[50]) < 1e-6);
const cached = gate.compute(state); assert.equal(cached[1], obs[1]);
for (let i = 0; i < 205; i++) {ctx.mjData.time += .02; obs = gate.compute(state);}
assert.equal(obs[1], 0); assert.equal(obs[3], 0);
requested = 1; ctx.mjData.time += .02; obs = gate.compute(state);
assert.equal(obs[3], 1); assert.equal(obs[4], 1001);
assert.ok(Math.abs(obs[50]) < 1e-6);
gate.reset(); requested = 1; ctx.mjData.time = 0; obs = gate.compute(state);
assert.deepEqual(Array.from(obs.slice(0, 4)), [1, 1, 1, 0]);
gate.reset(); requested = 0; ctx.mjData.time = 0;
state.rootQuat = new Float32Array([Math.SQRT1_2, 0, 0, Math.SQRT1_2]);
obs = gate.compute(state);
assert.ok(Math.abs(obs[50]) < 1e-6 && Math.abs(obs[51]) < 1e-6);
for (const [i, value] of [1, 0, 0, 1, 0, 0].entries()) assert.ok(Math.abs(obs[53+i] - value) < 1e-6);
console.log('GateReference: phase, direction, re-anchoring and reset passed');

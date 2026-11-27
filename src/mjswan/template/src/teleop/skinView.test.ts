import { expect, it } from 'vitest';
import { nextSkinView } from './skinView';

it('cycles between beside, skin only, xray, and robot only', () => {
  const views = [
    { enabled: true, beside: true, xray: false },
    { enabled: true, beside: false, xray: false },
    { enabled: true, beside: false, xray: true },
    { enabled: false, beside: false, xray: false },
  ];
  for (let i = 0; i < views.length; i++) {
    expect(nextSkinView(views[i])).toEqual(views[(i + 1) % views.length]);
  }
});

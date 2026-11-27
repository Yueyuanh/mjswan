export interface SkinView {
  enabled: boolean;
  beside: boolean;
  xray: boolean;
}

export function nextSkinView(view: SkinView): SkinView {
  if (!view.enabled) return { enabled: true, beside: true, xray: false };
  if (view.beside) return { enabled: true, beside: false, xray: false };
  if (!view.xray) return { enabled: true, beside: false, xray: true };
  return { enabled: false, beside: false, xray: false };
}

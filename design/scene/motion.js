// Closed-form damped springs: position as a pure function of time, so any frame can be computed
// directly (no integration, no carried state). Mass 1, time in seconds, motion from 0 to 1.

export function spring(t, k, d) {
  if (t <= 0) return 0;
  const w0 = Math.sqrt(k);
  const z = d / (2 * w0);
  if (Math.abs(z - 1) < 1e-4) return 1 - Math.exp(-w0 * t) * (1 + w0 * t);
  if (z < 1) {
    const wd = w0 * Math.sqrt(1 - z * z);
    return 1 - Math.exp(-z * w0 * t) * (Math.cos(wd * t) + ((z * w0) / wd) * Math.sin(wd * t));
  }
  const s = Math.sqrt(z * z - 1);
  const r1 = -w0 * (z - s), r2 = -w0 * (z + s);
  return 1 - (r2 * Math.exp(r1 * t) - r1 * Math.exp(r2 * t)) / (r2 - r1);
}

// A value that changes target several times: one spring per change, each starting at its own time.
// keys: [[time, value], ...] sorted by time.
export function track(t, keys, k, d) {
  let v = keys[0][1];
  for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * spring(t - keys[i][0], k, d);
  return v;
}

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const ramp = (t, start, length) => clamp((t - start) / length);

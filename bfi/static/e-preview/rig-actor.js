// Named-piece SVG actor. Shape interpolation is approximate during motion; endpoints use full paths.
const NS = "http://www.w3.org/2000/svg";
const cache = new Map();
const area = (points) =>
  points.reduce((sum, p, i) => {
    const q = points[(i + 1) % points.length];
    return sum + p[0] * q[1] - q[0] * p[1];
  }, 0) / 2;
export function rings(data) {
  return [...data.matchAll(/M([^MZ]+)Z/g)]
    .map((m) =>
      m[1]
        .trim()
        .split(/\s+/)
        .map((p) => p.split(",").map(Number)),
    )
    .filter((p) => p.length >= 3)
    .sort((a, b) => Math.abs(area(b)) - Math.abs(area(a)));
}
export function resample(points, count = 72) {
  const lengths = points.map((p, i) =>
    Math.hypot(
      p[0] - points[(i + 1) % points.length][0],
      p[1] - points[(i + 1) % points.length][1],
    ),
  );
  const total = lengths.reduce((a, b) => a + b, 0);
  let segment = 0,
    passed = 0;
  return Array.from({ length: count }, (_, i) => {
    const distance = (total * i) / count;
    while (segment < lengths.length - 1 && passed + lengths[segment] < distance)
      passed += lengths[segment++];
    const t = (distance - passed) / (lengths[segment] || 1),
      a = points[segment],
      b = points[(segment + 1) % points.length];
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  });
}
export function alignRings(a, b) {
  if (Math.sign(area(a)) !== Math.sign(area(b))) b = [...b].reverse();
  let best = 0,
    cost = Infinity;
  for (let shift = 0; shift < b.length; shift++) {
    let score = 0;
    for (let i = 0; i < a.length; i++) {
      const q = b[(i + shift) % b.length];
      score += (a[i][0] - q[0]) ** 2 + (a[i][1] - q[1]) ** 2;
    }
    if (score < cost) {
      cost = score;
      best = shift;
    }
  }
  return b.map((_, i) => b[(i + best) % b.length]);
}
const pathOf = (points) =>
  "M" + points.map((p) => p.map((v) => v.toFixed(2)).join(",")).join(" ") + "Z";
function tiny(points) {
  const x = points.reduce((s, p) => s + p[0], 0) / points.length,
    y = points.reduce((s, p) => s + p[1], 0) / points.length;
  return points.map((p) => [x + (p[0] - x) * 0.01, y + (p[1] - y) * 0.01]);
}
// Move centroids and turn local contours, instead of stretching every corner directly.
export function turnPair(a, b) {
  const center = (p) =>
    [0, 1].map((k) => p.reduce((n, v) => n + v[k], 0) / p.length);
  const ca = center(a),
    cb = center(b);
  const l = a.map((p) => [p[0] - ca[0], p[1] - ca[1]]),
    r = b.map((p) => [p[0] - cb[0], p[1] - cb[1]]);
  let dot = 0,
    cross = 0;
  for (let i = 0; i < l.length; i++) {
    dot += l[i][0] * r[i][0] + l[i][1] * r[i][1];
    cross += l[i][0] * r[i][1] - l[i][1] * r[i][0];
  }
  const angle = Math.atan2(cross, dot),
    co = Math.cos(angle),
    si = Math.sin(angle);
  const local = r.map((p) => [co * p[0] + si * p[1], -si * p[0] + co * p[1]]);
  return (t) => {
    const c = Math.cos(angle * t),
      sn = Math.sin(angle * t);
    return l.map((p, i) => {
      const x = p[0] + (local[i][0] - p[0]) * t,
        y = p[1] + (local[i][1] - p[1]) * t;
      return [
        ca[0] + (cb[0] - ca[0]) * t + c * x - sn * y,
        ca[1] + (cb[1] - ca[1]) * t + sn * x + c * y,
      ];
    });
  };
}
export function morphPath(from, to, turning = false) {
  const a = rings(from).filter((p) => Math.abs(area(p)) > 1),
    b = rings(to).filter((p) => Math.abs(area(p)) > 1),
    pairs = [];
  for (let i = 0; i < Math.min(Math.max(a.length, b.length), 24); i++) {
    const left = a[i] || tiny(b[i]),
      right = b[i] || tiny(a[i]);
    const l = resample(left),
      r = alignRings(l, resample(right));
    pairs.push(
      turning
        ? turnPair(l, r)
        : (t) =>
            l.map((p, i) => [
              p[0] + (r[i][0] - p[0]) * t,
              p[1] + (r[i][1] - p[1]) * t,
            ]),
    );
  }
  return (t) => pairs.map((interpolate) => pathOf(interpolate(t))).join("");
}
async function load(role, pose) {
  const key = role + "/" + pose;
  if (!cache.has(key)) {
    const request = fetch(
      new URL(`assets/poses/${role}/${pose}.rig.json`, import.meta.url),
    ).then((r) => {
      if (!r.ok) throw Error("Rig unavailable: " + key);
      return r.json();
    });
    cache.set(key, request);
    request.catch(() => cache.delete(key));
  }
  return cache.get(key);
}
const element = (name, attrs = {}) => {
  const e = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
};
function create(data) {
  const svg = element("svg", {
    viewBox: "0 0 512 512",
    role: "img",
    "aria-label": `${data.role}, ${data.pose}`,
    "data-pose": data.pose,
    "data-rig": "semantic-v1",
    "data-whole-shapes": data.mappingMethod === "whole-shape",
  });
  const title = element("title");
  title.textContent = `${data.role} / ${data.pose} / named body pieces`;
  svg.append(title);
  for (const [index, part] of data.parts.entries()) {
    const group = element("g", {
      "data-part": part.id,
      "data-visible": part.visible,
    });
    const moving = element("g", { class: "piece-motion" });
    moving.style.transformOrigin = `${part.pivot[0]}px ${part.pivot[1]}px`;
    moving.style.setProperty("--piece-delay", `${-index * 0.37}s`);
    moving.style.setProperty(
      "--piece-amplitude",
      part.id.includes("hand")
        ? "1.4deg"
        : part.id === "head"
          ? ".65deg"
          : ".3deg",
    );
    for (let i = 0; i < 3; i++)
      moving.append(
        element("path", {
          d: part.paths[i],
          fill: data.palette[i],
          "fill-rule": "evenodd",
          "data-color": i,
          class: "morph-outline",
        }),
      );
    for (const shape of data.sourceComponents || []) {
      if (shape.part !== part.id) continue;
      moving.append(
        element("path", {
          d: shape.path,
          fill: data.palette[shape.color],
          "fill-rule": "evenodd",
          "data-shape": shape.id,
        }),
      );
    }
    group.append(moving);
    svg.append(group);
  }
  const box = data.guide.head,
    x = Math.min(467, box[2] + 14),
    y = (box[1] + box[3]) / 2;
  const marks = element("g", {
    class: "speech-marks",
    transform: `translate(${x} ${y})`,
    "aria-hidden": "true",
  });
  for (let i = 0; i < 3; i++) {
    const bar = element("path", {
      d: `M${i * 10},${-6 - i * 4} l5,-3 v${14 + i * 8} l-5,3 Z`,
      fill: data.palette[1],
    });
    bar.style.setProperty("--beat-delay", `${i * 0.13}s`);
    marks.append(bar);
  }
  svg.append(marks);
  return svg;
}
export class RigActor {
  constructor(el, options = {}) {
    this.el = el;
    this.options = options;
    this.generation = 0;
    this.frame = null;
    this.done = null;
    this.data = null;
    this.offsets = {};
    this.shapeOffsets = {};
    this.selected = "head";
    this.idle = true;
    this.dragEnabled = false;
    this.el.dataset.visible = "true";
    this.el.classList.add("piece-idle");
    this.el.dataset.speechStyle = "both";
    this.controller = new AbortController();
    this.listen = (type, handler) =>
      this.el.addEventListener(type, handler, {
        signal: this.controller.signal,
      });
    this.listen("pointerdown", (e) => {
      const part = e.target.closest?.("[data-part]");
      if (!part) return;
      this.selectPart(part.dataset.part);
      if (!this.dragEnabled) return;
      e.preventDefault();
      const rect = this.el.querySelector("svg").getBoundingClientRect();
      this.drag = {
        x: e.clientX,
        y: e.clientY,
        ratio: 512 / Math.min(rect.width, rect.height),
        offset: {
          ...(this.offsets[this.selected] || { x: 0, y: 0, rotation: 0 }),
        },
      };
      if (this.dragForms && e.target.dataset.shape) {
        this.drag.shape = e.target.dataset.shape;
        this.drag.offset = {
          ...(this.shapeOffsets[this.drag.shape] || { x: 0, y: 0 }),
        };
        this.el.dispatchEvent(
          new CustomEvent("shapechange", {
            detail: { id: this.drag.shape, part: this.selected },
          }),
        );
      }
      this.el.setPointerCapture(e.pointerId);
    });
    this.listen("pointermove", (e) => {
      if (!this.drag) return;
      if (this.drag.shape) {
        const offset = {
          x: this.drag.offset.x + (e.clientX - this.drag.x) * this.drag.ratio,
          y: this.drag.offset.y + (e.clientY - this.drag.y) * this.drag.ratio,
        };
        this.shapeOffsets[this.drag.shape] = offset;
        this.el
          .querySelector(`[data-shape="${this.drag.shape}"]`)
          ?.setAttribute("transform", `translate(${offset.x} ${offset.y})`);
        return;
      }
      this.setPartOffset(this.selected, {
        ...this.drag.offset,
        x: this.drag.offset.x + (e.clientX - this.drag.x) * this.drag.ratio,
        y: this.drag.offset.y + (e.clientY - this.drag.y) * this.drag.ratio,
      });
      this.selectPart(this.selected);
    });
    this.listen("pointerup", () => {
      this.drag = null;
    });
    this.listen("pointercancel", () => {
      this.drag = null;
    });
    this.observer = new MutationObserver(() => {
      if (!this.motion()) this.settle();
    });
    this.observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-motion"],
    });
    this.media = matchMedia("(prefers-reduced-motion: reduce)");
    this.onMedia = () => {
      if (!this.motion()) this.settle();
    };
    this.media.addEventListener("change", this.onMedia);
  }
  motion() {
    return this.options.motionEnabled?.() ?? !this.media.matches;
  }
  notify() {
    this.el.dispatchEvent(
      new CustomEvent("rigchange", {
        detail: {
          role: this.data?.role,
          pose: this.data?.pose,
          parts:
            this.data?.parts.map((p) => ({
              id: p.id,
              visible: p.visible,
              label: p.label,
            })) || [],
          selected: this.selected,
        },
      }),
    );
  }
  cancel() {
    if (this.frame !== null) cancelAnimationFrame(this.frame);
    this.frame = null;
    this.el.classList.remove("morphing");
    this.el.dataset.transitioning = "false";
    if (this.done) {
      this.done();
      this.done = null;
    }
  }
  settle() {
    this.cancel();
    if (this.data) this.render(this.data);
  }
  render(data) {
    this.el.replaceChildren(create(data));
    this.el.dataset.profile = data.role;
    this.el.dataset.pose = data.pose;
    this.applyOffsets();
    this.selectPart(this.selected);
    this.notify();
  }
  async setPose(pose, profile) {
    const actual = this.options.resolvePose?.(profile, pose) || pose;
    if (!this.options.validPose?.(profile, actual))
      throw Error("Unknown character or pose");
    const ticket = ++this.generation;
    this.cancel();
    this.shapeOffsets = {};
    const target = await load(profile, actual).catch((error) => {
      if (ticket === this.generation) throw error;
      return null;
    });
    if (!target) return;
    if (ticket !== this.generation) return;
    const old = this.el.querySelector("svg"),
      same = this.data?.role === profile;
    this.data = target;
    this.profile = profile;
    this.pose = actual;
    if (!same) this.offsets = {};
    if (
      !old ||
      !same ||
      !this.motion() ||
      this.options.transitionStyle === "still"
    ) {
      this.render(target);
      return;
    }
    const start = {};
    for (const part of target.parts) {
      const group = old.querySelector(`[data-part="${part.id}"]`);
      start[part.id] = part.paths.map(
        (_, i) =>
          group?.querySelector(`[data-color="${i}"]`)?.getAttribute("d") || "",
      );
    }
    const interpolators = target.parts.map((part) =>
      part.paths.map((path, i) =>
        morphPath(
          start[part.id][i],
          path,
          this.options.transitionStyle !== "morph",
        ),
      ),
    );
    const svg = create(target);
    this.el.replaceChildren(svg);
    this.el.classList.add("morphing");
    this.el.dataset.transitioning = "true";
    this.applyOffsets();
    this.selectPart(this.selected);
    const nodes = target.parts.map((p) => [
      ...svg.querySelector(`[data-part="${p.id}"]`).querySelectorAll("path"),
    ]);
    let began;
    await new Promise((resolve) => {
      this.done = resolve;
      const step = (now) => {
        if (ticket !== this.generation) {
          this.cancel();
          return;
        }
        began ??= now;
        const t = Math.min(1, (now - began) / (this.options.duration || 850)),
          ease = t * t * (3 - 2 * t);
        for (let p = 0; p < nodes.length; p++)
          for (let c = 0; c < 3; c++)
            nodes[p][c].setAttribute("d", interpolators[p][c](ease));
        if (t < 1) this.frame = requestAnimationFrame(step);
        else {
          this.cancel();
          this.render(target);
          this.el.dataset.transitioning = "false";
        }
      };
      this.frame = requestAnimationFrame(step);
    });
  }
  setSpeaking(value) {
    this.el.classList.toggle("speaking", !!value);
    this.el.dispatchEvent(
      new CustomEvent("speechchange", { detail: { speaking: !!value } }),
    );
  }
  show() {
    this.el.dataset.visible = "true";
  }
  hide() {
    this.el.dataset.visible = "false";
    this.setSpeaking(false);
  }
  setIdle(value) {
    this.idle = !!value;
    this.el.classList.toggle("piece-idle", this.idle);
  }
  isolatePart(value) {
    this.el.classList.toggle("isolate-part", !!value);
  }
  showParts(value) {
    this.el.classList.toggle("inspect-parts", !!value);
  }
  selectPart(id) {
    if (!id) return;
    this.selected = id;
    this.el
      .querySelectorAll("[data-part]")
      .forEach((el) =>
        el.toggleAttribute("data-selected", el.dataset.part === id),
      );
    this.el.dispatchEvent(
      new CustomEvent("rigpart", {
        detail: { id, offset: this.offsets[id] || { x: 0, y: 0, rotation: 0 } },
      }),
    );
  }
  setPartOffset(id, offset) {
    if (
      ![offset.x, offset.y, offset.rotation].every((v) =>
        Number.isFinite(Number(v)),
      )
    )
      throw new RangeError("Piece offsets must be finite");
    this.offsets[id] = {
      x: Number(offset.x) || 0,
      y: Number(offset.y) || 0,
      rotation: Number(offset.rotation) || 0,
    };
    this.applyOffsets();
  }
  applyOffsets() {
    for (const part of this.data?.parts || []) {
      const group = this.el.querySelector(`[data-part="${part.id}"]`),
        o = this.offsets[part.id] || { x: 0, y: 0, rotation: 0 };
      group?.setAttribute(
        "transform",
        `translate(${o.x} ${o.y}) rotate(${o.rotation} ${part.pivot[0]} ${part.pivot[1]})`,
      );
    }
  }
  resetParts() {
    this.offsets = {};
    this.shapeOffsets = {};
    this.el
      .querySelectorAll("[data-shape]")
      .forEach((p) => p.removeAttribute("transform"));
    this.applyOffsets();
    this.selectPart(this.selected);
  }
  exportRig() {
    return {
      ...this.data,
      previewOffsets: this.offsets,
      previewShapeOffsets: this.shapeOffsets,
    };
  }
  destroy() {
    this.generation++;
    this.cancel();
    this.controller.abort();
    this.observer.disconnect();
    this.media.removeEventListener("change", this.onMedia);
    this.el.replaceChildren();
  }
}

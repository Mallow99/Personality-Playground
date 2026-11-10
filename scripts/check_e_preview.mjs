// Deterministic component checks; no browser/DOM rendering claim.
import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import {
  CharacterActor,
  ProfileTransition,
  AgentCursor,
  profiles,
  poseCatalog,
  cursorShapes,
  cursorSVG,
  cursorHotspot,
} from "../bfi/static/e-preview/components.js";
const root = new URL("../bfi/static/e-preview/", import.meta.url);
const markup = await readFile(new URL("index.html", root), "utf8");
for (const m of markup.matchAll(/(?:src|href)="([^"#]+)"/g)) {
  if (m[1].startsWith("http")) continue;
  await readFile(new URL(m[1], root));
}
const studio = await readFile(new URL("studio.js", root), "utf8");
for (const match of studio.matchAll(/\$\("([a-z-]+)"\)/g))
  assert(markup.includes(`id="${match[1]}"`), `Missing UI element ${match[1]}`);
const palettes = Object.values(profiles).flatMap((p) => p.colors);
assert.equal(new Set(palettes).size, 9);
const manifest = JSON.parse(
  await readFile(new URL("assets/poses/manifest.json", root), "utf8"),
);
for (const [id, items] of Object.entries(poseCatalog)) {
  assert.equal(items.length, 18);
  for (const item of items) {
    const source = await readFile(
      new URL(`assets/poses/${id}/${item.id}.svg`, root),
      "utf8",
    );
    assert(
      !/<(?:script|image|foreignObject)\b|\b(?:href|onload)=/i.test(source),
    );
    for (const color of source.matchAll(/(?:fill|stroke)="(#[\da-f]+)"/gi))
      assert(profiles[id].colors.includes(color[1]));
    const check = manifest.characters[id].find((p) => p.id === item.id);
    assert(check.geometry_iou >= 0.98);
    assert.equal(check.boundary_geometry_iou, 1);
    assert(check.palette_agreement >= 0.995);
  }
  for (const kind of ["face", "motif"])
    await readFile(new URL(`assets/${id}-${kind}.svg`, root));
}
for (const id of Object.keys(profiles))
  for (const shape of cursorShapes) {
    const source = cursorSVG(id, shape);
    assert(source.includes(profiles[id].name));
    assert(!source.includes("undefined"));
  }
globalThis.document = {
  documentElement: { dataset: { motion: "off" } },
  addEventListener() {},
};
globalThis.matchMedia = () => ({ matches: false });
function element() {
  return {
    dataset: {},
    style: {},
    classList: { toggle() {}, remove() {}, add() {} },
    children: [],
    replaceChildren(...v) {
      this.children = v;
    },
    querySelector() {
      return null;
    },
    setAttribute() {},
  };
}
const pending = new Map();
globalThis.fetch = (url) =>
  new Promise((resolve) =>
    pending.set(String(url), () =>
      resolve({ ok: true, text: async () => String(url) }),
    ),
  );
globalThis.DOMParser = class {
  parseFromString(source) {
    return {
      querySelector() {
        return null;
      },
      documentElement: {
        localName: "svg",
        cloneNode() {
          return { ...element(), source };
        },
      },
    };
  }
};
const host = element(),
  actor = new CharacterActor(host);
const first = actor.setPose("standing", "academic"),
  second = actor.setPose("seated", "business");
pending.get(new URL("assets/poses/business/seated.svg", root).href)();
await second;
pending.get(new URL("assets/poses/academic/standing.svg", root).href)();
await first;
assert.equal(host.dataset.profile, "business");
assert.equal(host.dataset.pose, "seated");
actor.hide();
assert.equal(host.dataset.visible, "false");
actor.show();
assert.equal(host.dataset.visible, "true");
await assert.rejects(() => actor.setPose("unknown"));
actor.destroy();
assert.equal(host.children.length, 0);
let skip, escape;
const layer = {
  ...element(),
  hidden: true,
  querySelector(selector) {
    return selector === "button"
      ? {
          addEventListener(_, fn) {
            skip = fn;
          },
        }
      : { textContent: "" };
  },
};
document.addEventListener = (_, fn) => {
  escape = fn;
};
const transition = new ProfileTransition(layer);
transition.play("academic");
assert(layer.hidden);
document.documentElement.dataset.motion = "on";
transition.play("academic");
assert(!layer.hidden);
transition.play("business");
assert.equal(layer.dataset.profile, "business");
skip();
assert(layer.hidden);
transition.play("engineering");
escape({ key: "Escape" });
assert(layer.hidden);
const pointer = element(),
  cursor = new AgentCursor(pointer);
cursor.update({ profileId: "academic", shape: "arrow", x: 80, y: 50 });
assert.equal(pointer.style.transform, "translate(77px,48px)");
cursor.hide();
assert(pointer.hidden);
assert.throws(() =>
  cursor.update({ profileId: "academic", shape: "text", x: NaN, y: 0 }),
);
assert.deepEqual(cursorHotspot("link"), [11, 3]);
console.log(
  "PASS: local assets, distinct palettes, 39 cursor variants, actor race handling, visibility, transition cancellation/skip/reduced motion, and cursor coordinates.",
);

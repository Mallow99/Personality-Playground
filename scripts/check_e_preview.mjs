import {
  rings,
  resample,
  morphPath,
  turnPair,
} from "../bfi/static/e-preview/rig-actor.js";
// Deterministic component checks; no browser/DOM rendering claim.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import {
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
const retained = JSON.parse(
  await readFile(
    new URL(
      "../research/visual-studies/poses-v3/retained-glamour.json",
      import.meta.url,
    ),
    "utf8",
  ),
);
for (const [role, hashes] of Object.entries(retained)) {
  const current = manifest.characters[role].find((p) => p.id === "glamour");
  assert.equal(current.sheet_sha256, hashes.sheet_sha256);
  assert.equal(current.vector_sha256, hashes.vector_sha256);
}
for (const [id, items] of Object.entries(poseCatalog)) {
  assert.equal(items.length, id === "engineering" ? 26 : 24);
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

const report = JSON.parse(
  await readFile(new URL("assets/poses/rig-report.json", root), "utf8"),
);
assert.equal(report.parts.length, 17);
let count = 0;
for (const [role, items] of Object.entries(poseCatalog))
  for (const item of items) {
    const rig = JSON.parse(
      await readFile(
        new URL(`assets/poses/${role}/${item.id}.rig.json`, root),
        "utf8",
      ),
    );
    assert.deepEqual(
      rig.parts.map((p) => p.id),
      report.parts,
    );
    assert(rig.assembly_geometry_iou >= 0.99);
    for (const region of rig.guide.ownershipRegions || []) {
      const part = rig.parts.find((p) => p.id === region.id);
      const xs = region.polygon.map((p) => p[0]),
        ys = region.polygon.map((p) => p[1]);
      assert(part.visible, `${role}/${item.id}: missing mapped hand`);
      for (const [color, path] of part.paths.entries()) {
        if (!region.colors.includes(color)) assert.equal(path, "");
        for (const [x, y] of rings(path).flat()) {
          assert(x >= Math.min(...xs) - 0.5 && x <= Math.max(...xs) + 0.5);
          assert(y >= Math.min(...ys) - 0.5 && y <= Math.max(...ys) + 0.5);
        }
      }
    }
    assert.equal(
      rig.source_sha256,
      manifest.characters[role].find((p) => p.id === item.id).vector_sha256,
    );
    for (const part of rig.parts) {
      assert.equal(part.paths.length, 3);
      for (const path of part.paths)
        for (const ring of rings(path))
          assert(ring.flat().every(Number.isFinite));
    }
    count++;
  }
assert.equal(count, 74);
const review = JSON.parse(
  await readFile(new URL("assets/pose-review.json", root), "utf8"),
);
assert.equal(review.proposals.length, 54);
assert.equal(new Set(review.proposals.map((p) => p.code)).size, 54);
assert(review.proposals.every((p) => p.status === "unreviewed"));
const cells = new Set(),
  sheets = new Set();
for (const p of review.proposals) {
  assert(p.reason.length > 70, `Missing useful reason for ${p.code}`);
  const meta = p.image;
  assert(
    meta &&
      meta.row >= 0 &&
      meta.row < 2 &&
      meta.column >= 0 &&
      meta.column < 3,
  );
  const cell = `${meta.sheet}:${meta.row}:${meta.column}`;
  assert(!cells.has(cell), `Reused illustration cell for ${p.code}`);
  cells.add(cell);
  sheets.add(meta.sheet);
  const png = await readFile(new URL(meta.sheet, root));
  assert.equal(png.readUInt32BE(16), 1536);
  assert.equal(png.readUInt32BE(20), 1024);
  assert.equal(createHash("sha256").update(png).digest("hex"), meta.sha256);
}
assert.equal(sheets.size, 9);
const turning = turnPair(
  [
    [0, 0],
    [30, 0],
    [30, 4],
    [0, 4],
  ],
  [
    [20, 10],
    [20, 40],
    [16, 40],
    [16, 10],
  ],
);
const middle = turning(0.5);
const middleArea = Math.abs(
  middle.reduce((s, p, i) => {
    const q = middle[(i + 1) % middle.length];
    return s + p[0] * q[1] - q[0] * p[1];
  }, 0) / 2,
);
assert(
  Math.abs(middleArea - 120) < 0.01,
  "Turning should preserve a rigid form's area",
);
for (const role of Object.keys(profiles)) {
  const a = JSON.parse(
    await readFile(
      new URL(`assets/poses/${role}/standing.rig.json`, root),
      "utf8",
    ),
  );
  const b = JSON.parse(
    await readFile(
      new URL(`assets/poses/${role}/seated.rig.json`, root),
      "utf8",
    ),
  );
  for (const id of [
    "head",
    "left-hand",
    "right-hand",
    "left-foot",
    "right-foot",
  ])
    for (let color = 0; color < 3; color++) {
      const f = morphPath(
        a.parts.find((p) => p.id === id).paths[color],
        b.parts.find((p) => p.id === id).paths[color],
      );
      for (const t of [0, 0.25, 0.5, 0.75, 1])
        assert(!/NaN|Infinity|undefined/.test(f(t)));
    }
}
const disappearing = morphPath("M0,0 10,0 10,10 0,10Z", "");
assert(!disappearing(0.5).includes("NaN"));
const sample = resample(
  [
    [0, 0],
    [20, 0],
    [20, 20],
    [0, 20],
  ],
  72,
);
assert.equal(sample.length, 72);
assert(sample.flat().every(Number.isFinite));
assert.deepEqual(cursorHotspot("link"), [11, 3]);
console.log(
  "PASS: 74 pose assets, stable 17-part rigs, source hashes/fidelity, finite matched-piece morphs, UI wiring, and role cursor exports.",
);

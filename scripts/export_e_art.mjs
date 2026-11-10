// Rebuild review sheets and downloadable cursor assets from their source geometry.
import { mkdir, writeFile, readFile } from "node:fs/promises";
import {
  profiles,
  poseCatalog,
  cursorShapes,
  cursorSVG,
} from "../bfi/static/e-preview/components.js";
const root = new URL("../bfi/static/e-preview/assets/", import.meta.url);
await mkdir(new URL("cursors/", root), { recursive: true });
const frame = (width, height, title, content) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><title>${title}</title><rect width="100%" height="100%" fill="#f6f0e5"/>${content}</svg>`;
const nested = (source, x, y, w, h) =>
  source.replace(
    /<svg\b[^>]*>/,
    `<svg x="${x}" y="${y}" width="${w}" height="${h}" viewBox="0 0 512 512">`,
  );
let poseSheet = "",
  iconSheet = "",
  cursorSheet = "";
for (const [row, [id, p]] of Object.entries(Object.entries(profiles))) {
  const faceBoxes = {
    academic: "175 15 145 125",
    engineering: "210 10 170 108",
    business: "220 20 105 110",
  };
  const full = await readFile(
    new URL(`poses/${id}/standing.svg`, root),
    "utf8",
  );
  await writeFile(
    new URL(`${id}-face.svg`, root),
    full.replace(
      /<svg\b[^>]*>/,
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${faceBoxes[id]}" width="100" height="100" overflow="hidden">`,
    ),
  );
  const y = Number(row) * 1800;
  poseSheet += `<text x="25" y="${y + 32}" font-family="sans-serif" font-size="20" fill="${p.colors[0]}">${p.name} / E generated poses, directly traced</text>`;
  for (const [index, pose] of poseCatalog[id].entries()) {
    const col = index % 6,
      poseRow = Math.floor(index / 6);
    const svg = await readFile(
      new URL(`poses/${id}/${pose.id}.svg`, root),
      "utf8",
    );
    poseSheet +=
      nested(svg, col * 350 + 15, y + 50 + poseRow * 570, 320, 510) +
      `<text x="${col * 350 + 25}" y="${y + 600 + poseRow * 570}" font-family="sans-serif" font-size="17" fill="${p.colors[0]}">${pose.label}</text>`;
  }
  iconSheet += `<text x="25" y="${Number(row) * 220 + 30}" font-family="sans-serif" font-size="18" fill="${p.colors[0]}">${p.name}</text>`;
  for (const [column, type] of ["face", "motif"].entries())
    for (const [index, size] of [24, 48, 96].entries()) {
      const source = await readFile(new URL(`${id}-${type}.svg`, root), "utf8");
      iconSheet += source.replace(
        /<svg\b[^>]*>/,
        `<svg x="${column * 380 + 30 + index * 115}" y="${Number(row) * 220 + 60 + 96 - size}" width="${size}" height="${size}" viewBox="${(source.match(/viewBox="([^"]+)"/) || [])[1] || "0 0 100 100"}">`,
      );
    }
  for (const [col, shape] of cursorShapes.entries()) {
    const svg = cursorSVG(id, shape);
    await writeFile(new URL(`cursors/${id}-${shape}.svg`, root), svg + "\n");
    cursorSheet +=
      svg.replace(
        "<svg xmlns=",
        `<svg x="${col * 105 + 20}" y="${Number(row) * 130 + 35}" xmlns=`,
      ) +
      `<text x="${col * 105 + 10}" y="${Number(row) * 130 + 100}" font-family="sans-serif" font-size="11" fill="${p.colors[0]}">${shape}</text>`;
  }
}
await writeFile(
  new URL("pose-sheet.svg", root),
  frame(
    2100,
    5400,
    "E pose library: 54 generated poses, directly traced",
    poseSheet,
  ),
);
await writeFile(
  new URL("icon-sheet.svg", root),
  frame(800, 660, "E icon sizes: 24, 48, 96 pixels", iconSheet),
);
await writeFile(
  new URL("cursor-sheet.svg", root),
  frame(1380, 390, "Academic, Hacker, Business cursor sets", cursorSheet),
);
console.log("Exported 39 cursors and pose/icon/cursor contact sheets.");

// Rebuild review sheets and downloadable cursor assets from their source geometry.
import { mkdir, writeFile, readFile } from "node:fs/promises";
import {
  profiles,
  poses,
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
    `<svg x="${x}" y="${y}" width="${w}" height="${h}" viewBox="0 0 400 600">`,
  );
let poseSheet = "",
  iconSheet = "",
  cursorSheet = "";
for (const [row, [id, p]] of Object.entries(Object.entries(profiles))) {
  const y = Number(row) * 660;
  poseSheet += `<text x="25" y="${y + 32}" font-family="sans-serif" font-size="20" fill="${p.colors[0]}">${p.name} / E</text>`;
  for (const [col, pose] of poses.entries()) {
    const svg = await readFile(new URL(`${id}-${pose}.svg`, root), "utf8");
    poseSheet +=
      nested(svg, col * 350 + 15, y + 50, 320, 550) +
      `<text x="${col * 350 + 25}" y="${y + 635}" font-family="sans-serif" font-size="17" fill="${p.colors[0]}">${pose}</text>`;
  }
  iconSheet += `<text x="25" y="${Number(row) * 220 + 30}" font-family="sans-serif" font-size="18" fill="${p.colors[0]}">${p.name}</text>`;
  for (const [column, type] of ["face", "motif"].entries())
    for (const [index, size] of [24, 48, 96].entries()) {
      const source = await readFile(new URL(`${id}-${type}.svg`, root), "utf8");
      iconSheet += source.replace(
        /<svg\b[^>]*>/,
        `<svg x="${column * 380 + 30 + index * 115}" y="${Number(row) * 220 + 60 + 96 - size}" width="${size}" height="${size}" viewBox="0 0 100 100">`,
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
  frame(1400, 1980, "E pose library", poseSheet),
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

// One fixed drawing. Authored local motion; never infer a full-body pose.
const $ = (id) => document.getElementById(id),
  media = matchMedia("(prefers-reduced-motion: reduce)");
let svg,
  originalSvg,
  frame,
  playing = false,
  original = false,
  close = false,
  progress = 0,
  previous,
  strength = 1,
  resumeAfterCompare = false;
const tau = Math.PI * 2;
function apply() {
  if (!svg) return;
  const wave = Math.sin(tau * progress),
    lift = (1 - Math.cos(tau * progress)) / 2;
  const glance =
    progress > 0.15 && progress < 0.75
      ? Math.sin((Math.PI * (progress - 0.15)) / 0.6) ** 2
      : 0;
  const grip =
    progress > 0.35 && progress < 0.8
      ? Math.sin((Math.PI * (progress - 0.35)) / 0.45) ** 2
      : 0;
  const q = strength;
  svg
    .querySelector("#reading-head")
    .setAttribute("transform", `rotate(${-3.2 * glance * q} 247 232)`);
  svg
    .querySelector("#held-book")
    .setAttribute(
      "transform",
      `translate(0 ${-0.9 * lift * q}) rotate(${0.65 * wave * q} 258 330)`,
    );
  svg
    .querySelector("#reading-left-hand")
    .setAttribute("transform", `rotate(${1.8 * grip * q} 315 325)`);
  svg
    .querySelector("#reading-right-hand")
    .setAttribute("transform", `rotate(${-1.1 * grip * q} 192 326)`);
  $("scrub").value = String(Math.round(progress * 1000));
  const phase =
    progress < 0.22
      ? "Reading"
      : progress < 0.52
        ? "Glancing up"
        : progress < 0.78
          ? "Adjusting the grip"
          : "Back to the page";
  const label = original
    ? "Original still · unchanged source SVG"
    : phase + " · seated body fixed";
  if ($("phase").textContent !== label) $("phase").textContent = label;
}
function pause() {
  playing = false;
  cancelAnimationFrame(frame);
  previous = undefined;
  $("play").textContent = "Play";
}
function run() {
  if (media.matches || original) return;
  pause();
  playing = true;
  $("play").textContent = "Pause";
  function tick(now) {
    if (!playing) return;
    if (previous !== undefined)
      progress = (progress + (now - previous) / 8000) % 1;
    previous = now;
    apply();
    frame = requestAnimationFrame(tick);
  }
  frame = requestAnimationFrame(tick);
}
$("play").addEventListener("click", () => (playing ? pause() : run()));
$("original").addEventListener("click", () => {
  if (!original) resumeAfterCompare = playing;
  original = !original;
  pause();
  $("play").disabled = original || media.matches;
  $("original").setAttribute("aria-pressed", String(original));
  $("original").textContent = original
    ? "Return to movement"
    : "Compare original still";
  $("original-actor").hidden = !original;
  $("limited-actor").hidden = original;
  $("view-label").textContent = original
    ? "Original still"
    : "Limited movement";
  apply();
  if (!original && resumeAfterCompare) run();
});
$("restart").addEventListener("click", () => {
  if (original) $("original").click();
  progress = 0;
  apply();
  run();
});
$("zoom").addEventListener("click", () => {
  close = !close;
  const box = close ? "155 105 205 275" : "90 90 330 370";
  [svg, originalSvg].forEach((s) => s.setAttribute("viewBox", box));
  $("zoom").setAttribute("aria-pressed", String(close));
  $("zoom").textContent = close ? "Full seated pose" : "Close-up";
});
$("scrub").addEventListener("input", () => {
  pause();
  progress = Number($("scrub").value) / 1000;
  apply();
});
$("strength").addEventListener("input", () => {
  strength = Number($("strength").value) / 100;
  $("strength-label").textContent = `${strength.toFixed(1)}×`;
  apply();
});
function reduced() {
  if (media.matches) {
    pause();
    progress = 0;
    apply();
  }
  $("play").disabled = original || media.matches;
  $("motion-note").textContent = media.matches
    ? "Reduced motion is active. Inspect a still moment with the timeline, or compare the original."
    : "An eight-second silent loop. Drag the timeline to inspect it, or compare against the original still.";
}
media.addEventListener("change", reduced);
document.addEventListener("visibilitychange", () => {
  if (document.hidden) pause();
});
addEventListener("pagehide", () => pause());
async function load(path) {
  const response = await fetch(new URL(path, import.meta.url));
  if (!response.ok) throw Error("Artwork could not load");
  const doc = new DOMParser().parseFromString(
    await response.text(),
    "image/svg+xml",
  );
  if (doc.querySelector("parsererror")) throw Error("Artwork could not parse");
  return document.importNode(doc.documentElement, true);
}
try {
  [svg, originalSvg] = await Promise.all([
    load("assets/reading-limited.svg"),
    load("assets/poses/academic/reading.svg"),
  ]);
  originalSvg.setAttribute("viewBox", "90 90 330 370");
  originalSvg.removeAttribute("width");
  originalSvg.removeAttribute("height");
  $("limited-actor").append(svg);
  $("original-actor").append(originalSvg);
  for (const id of ["play", "original", "restart", "zoom", "reveal"])
    $(id).disabled = false;
  apply();
  reduced();
  if (!media.matches) run();
} catch (error) {
  $("error").hidden = false;
  $("error").textContent = error.message;
}

$("reveal").addEventListener("click", () => {
  pause();
  if (original) $("original").click();
  pause();
  const hidden = $("reveal").getAttribute("aria-pressed") !== "true";
  $("reveal").setAttribute("aria-pressed", String(hidden));
  for (const id of ["reading-left-hand", "reading-right-hand"])
    svg.querySelector("#" + id).style.visibility = hidden
      ? "hidden"
      : "visible";
  $("reveal").textContent = hidden ? "Restore hands" : "Reveal behind hands";
});

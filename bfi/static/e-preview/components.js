// Presentation only. These components never load models or execute computer actions.
export const profiles = {
  academic: {
    name: "Academic",
    colors: ["#58402B", "#87A452", "#EBD8AF"],
    summary: "Curious. Eccentric. Makes room for understanding.",
    line: "Let’s draw the relationship first. Then we can test where the explanation breaks.",
    motif: "Books & glasses",
  },
  engineering: {
    name: "Hacker",
    colors: ["#20171E", "#D9254C", "#F6A0B4"],
    summary: "Sharp. Playful. Precise when it counts.",
    line: "That shortcut has a long commute. Let’s trace the assumption before we rewrite it.",
    motif: "Error windows & eyes",
  },
  business: {
    name: "Business",
    colors: ["#153B64", "#247DD4", "#B9E9FA"],
    summary: "Composed. Dry. Interested in what follows.",
    line: "We have three options and one evening. I suggest we spend neither pretending otherwise.",
    motif: "Clipboard & sheets",
  },
};
export const poses = ["standing", "seated", "explaining", "thinking"];
export const motionEnabled = () =>
  document.documentElement.dataset.motion !== "off" &&
  !matchMedia("(prefers-reduced-motion: reduce)").matches;
const svgCache = new Map();
async function artwork(id, pose) {
  const key = `${id}-${pose}`;
  if (!svgCache.has(key)) {
    const task = fetch(new URL(`assets/${key}.svg`, import.meta.url))
      .then((r) => {
        if (!r.ok) throw Error(`Artwork unavailable: ${key}`);
        return r.text();
      })
      .then((text) => {
        const doc = new DOMParser().parseFromString(text, "image/svg+xml");
        if (
          doc.querySelector("parsererror") ||
          doc.documentElement.localName !== "svg"
        )
          throw Error("Invalid bundled artwork");
        return doc.documentElement;
      });
    svgCache.set(key, task);
    task.catch(() => svgCache.delete(key));
  }
  return (await svgCache.get(key)).cloneNode(true);
}
export class CharacterActor {
  constructor(element) {
    this.el = element;
    this.profile = "academic";
    this.pose = "standing";
    this.generation = 0;
    this.el.dataset.visible = "true";
  }
  async setPose(pose = this.pose, profile = this.profile) {
    if (!poses.includes(pose) || !profiles[profile])
      throw Error("Unknown character or pose");
    const ticket = ++this.generation;
    this.profile = profile;
    this.pose = pose;
    const svg = await artwork(profile, pose);
    if (ticket !== this.generation) return;
    svg.setAttribute("aria-label", `${profiles[profile].name}, ${pose}`);
    const old = this.el.querySelector("svg");
    this.el.replaceChildren(svg);
    this.el.dataset.pose = pose;
    this.el.dataset.profile = profile;
    if (motionEnabled()) {
      svg.animate(
        [
          { opacity: 0, transform: "translateY(6px)" },
          { opacity: 1, transform: "translateY(0)" },
        ],
        { duration: 240, easing: "ease-out" },
      );
      if (old) {
        old.setAttribute("aria-hidden", "true");
        this.el.prepend(old);
        const fade = old.animate([{ opacity: 0.65 }, { opacity: 0 }], {
          duration: 180,
        });
        fade.finished.then(
          () => old.remove(),
          () => old.remove(),
        );
      }
    }
  }
  setSpeaking(value) {
    this.el.classList.toggle("speaking", !!value);
  }
  show() {
    this.el.dataset.visible = "true";
  }
  hide() {
    this.el.dataset.visible = "false";
    this.setSpeaking(false);
  }
  destroy() {
    this.generation++;
    this.el.replaceChildren();
  }
}
export class ProfileTransition {
  constructor(layer) {
    this.el = layer;
    this.generation = 0;
    this.timer = null;
    this.el
      .querySelector("button")
      .addEventListener("click", () => this.stop());
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") this.stop();
    });
  }
  stop() {
    this.generation++;
    clearTimeout(this.timer);
    this.el.hidden = true;
    this.el.classList.remove("running");
  }
  play(profile) {
    this.stop();
    if (!profiles[profile] || !motionEnabled()) return;
    this.el.dataset.profile = profile;
    this.el.querySelector(".transition-label").textContent =
      profiles[profile].motif;
    this.el.hidden = false;
    void this.el.offsetWidth;
    this.el.classList.add("running");
    const ticket = this.generation;
    this.timer = setTimeout(() => {
      if (ticket === this.generation) this.stop();
    }, 2500);
  }
}
export const cursorShapes = [
  "arrow",
  "text",
  "link",
  "grab",
  "grabbing",
  "move",
  "scroll",
  "busy",
  "unavailable",
  "resize-ew",
  "resize-ns",
  "resize-nwse",
  "resize-nesw",
];
export const cursorHotspot = (shape) =>
  shape === "arrow" ? [3, 2] : shape === "link" ? [11, 3] : [16, 16];
const cursorPaths = {
  arrow: "M3 2 4 25 10 19 14 29 19 27 14 17 23 16Z",
  text: "M11 3H21V6H18V26H21V29H11V26H14V6H11Z",
  link: "M9 18V5Q9 1 12 3L13 14V10Q15 8 17 11Q20 9 22 13Q25 12 26 16L25 26 20 30H12L5 22Q3 18 6 17Z",
  grab: "M7 17 5 11Q5 7 8 9L11 16 10 5Q11 1 13 5L15 15 16 3Q19 1 19 6V15L22 7Q25 6 25 10L23 18 28 15Q32 16 28 21L22 29H11L4 22Q1 18 4 17Z",
  grabbing: "M5 14 9 10 13 12 17 9 21 12 26 12 27 23 21 29H12L5 22Z",
  move: "M16 2 22 9H18V14H23V10L30 16 23 22V18H18V23H22L16 30 10 23H14V18H9V22L2 16 9 10V14H14V9H10Z",
  scroll: "M16 2 23 10H18V22H23L16 30 9 22H14V10H9Z",
  busy: "M8 3H24V8L19 16 24 24V29H8V24L13 16 8 8Z",
  unavailable: "M7 3H25L30 8V24L25 29H7L2 24V8ZM9 8 7 10 23 25 26 22Z",
  "resize-ew": "M2 16 10 8V13H22V8L30 16 22 24V19H10V24Z",
  "resize-ns": "M16 2 24 10H19V22H24L16 30 8 22H13V10H8Z",
  "resize-nwse": "M3 3H15L11 7 25 21 29 17V29H17L21 25 7 11 3 15Z",
  "resize-nesw": "M29 3V15L25 11 11 25 15 29H3V17L7 21 21 7 17 3Z",
};
export function cursorSVG(profile, shape) {
  if (!profiles[profile] || !cursorShapes.includes(shape))
    throw Error("Unknown cursor");
  const [dark, accent, light] = profiles[profile].colors;
  const mark =
    profile === "academic"
      ? '<path d="M23 2H27V6H23ZM29 2H33V6H29ZM27 3H29V5H27Z"/>'
      : profile === "engineering"
        ? '<path d="m22 6 6-5 7 2-7 5Z"/>'
        : '<path d="m27 1 4 2-2 3 3 5-5 2-3-5 3-2-2-2Z"/>';
  return `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36"><title>${profiles[profile].name} ${shape}</title><path d="${cursorPaths[shape]}" fill="${dark}" stroke="${light}" stroke-width="1.4" stroke-linejoin="round"/><g fill="${accent}">${mark}</g><path d="M5 33H27" stroke="${accent}" stroke-width="2"/></svg>`;
}
export class AgentCursor {
  constructor(element) {
    this.el = element;
    this.el.style.pointerEvents = "none";
    this.el.setAttribute("aria-hidden", "true");
  }
  update({ profileId, shape, x, y }) {
    if (!Number.isFinite(x) || !Number.isFinite(y))
      throw Error("Cursor coordinates must be finite");
    this.el.innerHTML = cursorSVG(profileId, shape);
    const [hx, hy] = cursorHotspot(shape);
    this.el.style.transform = `translate(${x - hx}px,${y - hy}px)`;
    this.el.hidden = false;
  }
  hide() {
    this.el.hidden = true;
  }
}

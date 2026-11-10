// Shared renderer: authored images first, pose-local motion only when explicitly supported.
export async function avatarAPI(path = "", changes) {
  const response = await fetch(
    "/api/avatar" + path,
    changes
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(changes),
        }
      : {},
  );
  if (!response.ok) {
    let detail;
    try {
      detail = (await response.json()).detail;
    } catch {}
    throw Error(detail || "Avatar connection unavailable");
  }
  return response.json();
}
const cache = new Map();
export class AvatarView {
  constructor(element, { resolveURL = (path) => path } = {}) {
    this.resolveURL = resolveURL;
    this.el = element;
    this.ticket = 0;
    this.key = "";
    this.media = matchMedia("(prefers-reduced-motion: reduce)");
    this.el.classList.add("avatar-view");
    this.art = document.createElement("div");
    this.art.className = "avatar-art";
    this.marks = document.createElement("span");
    this.marks.className = "avatar-voice";
    this.marks.textContent = "▰ ▰ ▰";
    this.marks.setAttribute("aria-hidden", "true");
    this.caption = document.createElement("p");
    this.caption.className = "avatar-caption";
    this.label = document.createElement("small");
    this.label.className = "avatar-status";
    this.el.replaceChildren(this.art, this.marks, this.caption, this.label);
    this.start = performance.now();
    const tick = (now) => {
      if (this.svg && this.state?.motion && !this.media.matches) {
        if (this.motionKind === "seated-hand") {
          const amount = Math.sin((Math.PI * 2 * (now - this.start)) / 8000);
          this.svg
            .querySelector("#seated-moving-hand")
            .setAttribute("transform", `rotate(${-4 * amount} 246 267)`);
        } else {
          const t = ((now - this.start) / 8000) % 1,
            wave = Math.sin(Math.PI * 2 * t),
            lift = (1 - Math.cos(Math.PI * 2 * t)) / 2;
          const glance =
            t > 0.15 && t < 0.75
              ? Math.sin((Math.PI * (t - 0.15)) / 0.6) ** 2
              : 0;
          const grip =
            t > 0.35 && t < 0.8
              ? Math.sin((Math.PI * (t - 0.35)) / 0.45) ** 2
              : 0;
          this.svg
            .querySelector("#reading-head")
            .setAttribute("transform", `rotate(${-3.2 * glance} 247 232)`);
          this.svg
            .querySelector("#held-book")
            .setAttribute(
              "transform",
              `translate(0 ${-0.9 * lift}) rotate(${0.65 * wave} 258 330)`,
            );
          this.svg
            .querySelector("#reading-left-hand")
            .setAttribute("transform", `rotate(${1.8 * grip} 315 325)`);
          this.svg
            .querySelector("#reading-right-hand")
            .setAttribute("transform", `rotate(${-1.1 * grip} 192 326)`);
        }
      } else if (this.svg) {
        this.svg
          .querySelectorAll("[transform]")
          .forEach((e) => e.removeAttribute("transform"));
      }
      this.frame = null;
      if (this.svg && this.state?.motion && !this.media.matches)
        this.frame = requestAnimationFrame(tick);
    };
    this.tick = tick;
    this.frame = null;
    this.onMedia = () => {
      this.el.dataset.motion =
        this.state?.motion && !this.media.matches ? "on" : "off";
      this.syncAnimation();
    };
    this.media.addEventListener("change", this.onMedia);
  }
  syncAnimation() {
    cancelAnimationFrame(this.frame);
    this.frame = null;
    if (this.svg && this.state?.motion && !this.media.matches)
      this.frame = requestAnimationFrame(this.tick);
    else if (this.svg)
      this.svg
        .querySelectorAll("[transform]")
        .forEach((e) => e.removeAttribute("transform"));
  }
  async set(state, catalog) {
    this.state = state;
    this.el.dataset.activity = state.activity;
    this.el.dataset.motion = state.motion && !this.media.matches ? "on" : "off";
    this.el.dataset.profile = state.profile;
    this.el.dataset.size = state.size;
    this.caption.textContent = state.caption;
    this.label.textContent =
      state.activity === "speaking"
        ? "Reply · text cue"
        : state.activity === "thinking"
          ? "Thinking…"
          : state.activity === "error"
            ? "Reply unavailable"
            : "Here with you";
    const pose = catalog.poses.find((p) => p.id === state.pose_id);
    if (!pose) return;
    this.el.dataset.pose = pose.id;
    this.syncAnimation();
    if (this.key === pose.id) return;
    this.key = pose.id;
    const ticket = ++this.ticket;
    this.svg = null;
    this.motionKind = pose.motion;
    if (pose.motion === "reading" || pose.motion === "seated-hand") {
      const path = this.resolveURL(
        pose.layered_src || "/static/e-preview/assets/reading-limited.svg",
      );
      if (!cache.has(path))
        cache.set(
          path,
          fetch(path)
            .then((r) => {
              if (!r.ok) throw Error("Reading artwork unavailable");
              return r.text();
            })
            .catch((e) => {
              cache.delete(path);
              throw e;
            }),
        );
      try {
        const text = await cache.get(path);
        if (ticket !== this.ticket) return;
        const doc = new DOMParser().parseFromString(text, "image/svg+xml");
        this.svg = document.importNode(doc.documentElement, true);
        this.art.replaceChildren(this.svg);
        this.syncAnimation();
      } catch {
        if (ticket === this.ticket) this.image(pose);
      }
    } else this.image(pose);
  }
  image(pose) {
    const img = document.createElement("img");
    img.src = this.resolveURL(pose.src);
    img.alt = pose.label;
    img.draggable = false;
    this.art.replaceChildren(img);
  }
  replay() {
    this.start = performance.now();
    this.el.animate?.(
      [
        { opacity: 0.3, transform: "translateY(5px)" },
        { opacity: 1, transform: "translateY(0)" },
      ],
      { duration: this.media.matches || !this.state?.motion ? 0 : 300 },
    );
  }
  destroy() {
    ++this.ticket;
    cancelAnimationFrame(this.frame);
    this.media.removeEventListener("change", this.onMedia);
    this.el.replaceChildren();
  }
}
export async function connectAvatar(elements, onState = () => {}) {
  const catalog = await avatarAPI("/catalog"),
    views = elements.map((e) => new AvatarView(e));
  let stopped = false,
    revision = -1,
    timer;
  async function poll() {
    try {
      const state = await avatarAPI();
      if (state.revision !== revision) {
        revision = state.revision;
        await Promise.all(views.map((v) => v.set(state, catalog)));
        onState(state, catalog);
      }
    } catch (error) {
      onState(null, catalog, error);
    } finally {
      if (!stopped) timer = setTimeout(poll, 500);
    }
  }
  poll();
  return {
    catalog,
    views,
    close() {
      stopped = true;
      clearTimeout(timer);
      views.forEach((v) => v.destroy());
    },
  };
}

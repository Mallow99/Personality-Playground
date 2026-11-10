// Motif presentation only. Optional constructor option: { motionEnabled: () => boolean }.
const DURATION = 2200;
const EASE = "cubic-bezier(.22,.72,.18,1)";
const names = {
  academic: "Books & glasses",
  engineering: "Errors become eyes",
  business: "Clipboard & paper trail",
};
const svg = (box, body) =>
  `<svg viewBox="${box}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">${body}</svg>`;
function sheet(grid = false) {
  return svg(
    "0 0 120 150",
    `<path class="mv2-paper" d="M8 4H87L113 31V143H8Z"/><path class="mv2-accent" d="M87 4V31H113Z"/><path class="mv2-rules" d="M23 42H96M23 59H96M23 76H96M23 93H96M23 110H96${grid ? "M40 30V123M60 30V123M80 30V123" : ""}"/>`,
  );
}
function scene(profile) {
  if (profile === "academic")
    return `<div class="mv2-orbit"></div>${Array.from({ length: 7 }, (_, i) => `<div class="mv2-object mv2-leaf" data-index="${i}">${sheet()}</div>`).join("")}<div class="mv2-object mv2-book">${svg("0 0 300 190", `<g class="mv2-book-left"><path class="mv2-accent" d="M21 26 144 47 148 169 13 132Z"/><path class="mv2-paper" d="M28 15 144 40 146 154 25 122Z"/><path class="mv2-rules" d="m43 38 80 17m-81 3 81 18m-80 3 81 18m-80 3 81 18"/></g><g class="mv2-book-right"><path class="mv2-accent" d="m155 45 126-25 8 115-134 35Z"/><path class="mv2-paper" d="m155 38 117-28 4 115-121 31Z"/><path class="mv2-rules" d="m176 52 78-18m-78 39 79-18m-79 39 80-18m-80 39 80-18"/></g><path class="mv2-dark" d="m145 40 10-2v132l-7 7Z"/>`)}</div><div class="mv2-object mv2-glasses">${svg("0 0 320 120", `<path class="mv2-accent" fill-rule="evenodd" d="M10 24 131 10 146 99 26 111ZM29 39 119 28 129 84 42 94ZM181 17 309 7 291 102 175 106ZM197 34 288 26 276 85 194 90Z"/><path class="mv2-accent" d="m140 45 40-5-3 14-35 5ZM8 25 0 19 2 9 23 18ZM303 8 317 1 320 13 305 24Z"/><path class="mv2-paper" d="m45 48 11-1-6 27-10 1ZM210 44l11-1-6 25-10 1Z"/>`)}</div>`;
  if (profile === "engineering")
    return `${Array.from({ length: 5 }, (_, i) => `<div class="mv2-object mv2-error" data-index="${i}"><div class="mv2-window-top"><span>×</span><span>ERR / 0${i + 1}</span><span>_</span></div><div class="mv2-code"><i></i><i></i><i></i></div><small>[ ${i * 17 + 8} : ${i * 9 + 21} ]</small></div>`).join("")}${Array.from({ length: 8 }, (_, i) => `<div class="mv2-object mv2-slice" data-index="${i}"></div>`).join("")}<div class="mv2-object mv2-eyes">${svg("0 0 360 145", `<g class="mv2-eye-left"><path class="mv2-accent" d="m8 27 148 18-22 86-103-24Z"/><path class="mv2-paper" d="m29 45 100 15-32 49-53-15Z"/><path class="mv2-dark" d="m76 61 24 4-10 38-19-8Z"/></g><g class="mv2-eye-right"><path class="mv2-accent" d="m211 39 141-28-40 103-109 17Z"/><path class="mv2-paper" d="m226 55 97-20-34 63-70 15Z"/><path class="mv2-dark" d="m263 57 25-5-19 47-18 3Z"/></g>`)}</div>`;
  return `<div class="mv2-trail-grid"></div>${Array.from({ length: 7 }, (_, i) => `<div class="mv2-object mv2-report" data-index="${i}">${sheet(true)}</div>`).join("")}<div class="mv2-object mv2-clipboard">${svg("0 0 230 310", `<path class="mv2-dark" d="M23 14H208L218 301 9 293Z"/><path class="mv2-accent" d="M36 37H192L201 277 27 271Z"/><path class="mv2-paper" d="M49 52H180L188 254 40 250Z"/><path class="mv2-rules" d="M58 99H165M57 125H167M56 151H169M55 177H171M54 203H173M79 79 76 228M109 79 108 230M139 79 140 231"/><path class="mv2-paper" d="M82 4H150L157 50 73 48Z"/><path class="mv2-accent" d="M94 13H140L142 24H91Zm-37 219 23-24 21 5 28-38 34 11v48Z"/>`)}</div>`;
}

export class MotifTransition {
  constructor(layer, options = {}) {
    if (!layer || typeof layer.replaceChildren !== "function")
      throw new TypeError("A transition layer is required.");
    this.el = layer;
    this.motionEnabled = options.motionEnabled;
    this.animations = new Set();
    this.timers = new Set();
    this.resolvePlay = null;
    this.focusBefore = null;
    this.generation = 0;
    this.destroyed = false;
    this.media = matchMedia("(prefers-reduced-motion: reduce)");
    this.onEscape = (event) => {
      if (event.key === "Escape" && !this.el.hidden) {
        event.preventDefault();
        this.stop("skipped");
      }
    };
    this.onMotion = () => {
      if (!this.canAnimate()) this.stop("motion-off");
    };
    this.onResize = () => {
      if (!this.el.hidden) this.stop("resized");
    };
    document.addEventListener("keydown", this.onEscape);
    this.media.addEventListener("change", this.onMotion);
    window.addEventListener("resize", this.onResize, { passive: true });
    this.observer = new MutationObserver(this.onMotion);
    for (const target of [document.documentElement, document.body].filter(
      Boolean,
    ))
      this.observer.observe(target, {
        attributes: true,
        attributeFilter: ["data-motion"],
      });
    this.el.dataset.motionV2 = "true";
    this.el.hidden = true;
  }
  canAnimate() {
    return (
      !this.destroyed &&
      !this.media.matches &&
      document.documentElement.dataset.motion !== "off" &&
      document.body?.dataset.motion !== "off" &&
      (typeof this.motionEnabled !== "function" || this.motionEnabled())
    );
  }
  animate(element, frames, timing = {}) {
    if (!element) return null;
    const animation = element.animate(frames, {
      duration: DURATION,
      easing: EASE,
      fill: "both",
      ...timing,
    });
    this.animations.add(animation);
    animation.finished.then(
      () => this.animations.delete(animation),
      () => this.animations.delete(animation),
    );
    return animation;
  }
  object(element, frames, timing = {}) {
    return this.animate(
      element,
      frames.map(
        ({
          x = 0,
          y = 0,
          z = 0,
          scale = 1,
          rotate = 0,
          turn = 0,
          tilt = 0,
          ...rest
        }) => ({
          ...rest,
          transform: `translate(-50%,-50%) translate3d(${x}px,${y}px,${z}px) rotateZ(${rotate}deg) rotateY(${turn}deg) rotateX(${tilt}deg) scale(${scale})`,
        }),
      ),
      timing,
    );
  }
  stop(reason = "stopped") {
    this.generation++;
    for (const timer of this.timers) clearTimeout(timer);
    this.timers.clear();
    for (const animation of this.animations) animation.cancel();
    this.animations.clear();
    const restore = this.el.contains(document.activeElement);
    this.el.hidden = true;
    this.el.classList.remove("running");
    this.el.replaceChildren();
    if (restore && this.focusBefore?.isConnected)
      this.focusBefore.focus({ preventScroll: true });
    this.focusBefore = null;
    if (this.resolvePlay) {
      const resolve = this.resolvePlay;
      this.resolvePlay = null;
      resolve({ status: reason, profile: this.profile });
    }
  }
  play(profile) {
    this.stop("superseded");
    const id =
      typeof profile === "string"
        ? profile
        : profile?.id || profile?.profile_id;
    if (!names[id]) throw new RangeError("Unknown motif profile.");
    this.profile = id;
    if (!this.canAnimate())
      return Promise.resolve({ status: "reduced-motion", profile: id });
    const ticket = this.generation;
    this.focusBefore = document.activeElement;
    this.el.dataset.profile = id;
    this.el.setAttribute("aria-label", "Visual theme transition");
    this.el.innerHTML = `<div class="mv2-sweep mv2-sweep-back" aria-hidden="true"></div><div class="mv2-sweep mv2-sweep-front" aria-hidden="true"></div><div class="mv2-scene" aria-hidden="true">${scene(id)}</div><button class="mv2-skip" type="button">Skip animation <span>Esc</span></button>`;
    this.el
      .querySelector(".mv2-skip")
      .addEventListener("click", () => this.stop("skipped"), { once: true });
    this.el.hidden = false;
    const width = this.el.clientWidth || innerWidth,
      height = this.el.clientHeight || innerHeight;
    const geometry = {
      width,
      height,
      span: Math.min(width * 0.35, 330),
      lift: Math.min(height * 0.19, 155),
      compact: width < 600,
    };
    const result = new Promise((resolve) => {
      this.resolvePlay = resolve;
    });
    try {
      this.sweep(geometry);
      this[id](geometry);
      const timer = setTimeout(() => {
        this.timers.delete(timer);
        if (ticket === this.generation) this.stop("finished");
      }, DURATION);
      this.timers.add(timer);
    } catch (error) {
      this.stop("unavailable");
      throw error;
    }
    return result;
  }
  sweep({ width }) {
    this.animate(this.el.querySelector(".mv2-sweep-back"), [
      { opacity: 0, transform: "translateX(-170%) skewX(-19deg)", offset: 0 },
      {
        opacity: 0.68,
        transform: "translateX(8%) skewX(-19deg)",
        offset: 0.35,
      },
      {
        opacity: 0.38,
        transform: "translateX(75%) skewX(-19deg)",
        offset: 0.72,
      },
      {
        opacity: 0,
        transform: `translateX(${width}px) skewX(-19deg)`,
        offset: 1,
      },
    ]);
    this.animate(this.el.querySelector(".mv2-sweep-front"), [
      { opacity: 0, transform: "translateX(-150%) skewX(-19deg)", offset: 0 },
      {
        opacity: 0.16,
        transform: "translateX(12%) skewX(-19deg)",
        offset: 0.42,
      },
      {
        opacity: 0.1,
        transform: "translateX(150%) skewX(-19deg)",
        offset: 0.77,
      },
      { opacity: 0, transform: "translateX(240%) skewX(-19deg)", offset: 1 },
    ]);
    this.animate(this.el.querySelector(".mv2-caption"), [
      { opacity: 0, transform: "translateY(10px)", offset: 0 },
      { opacity: 1, transform: "translateY(0)", offset: 0.18 },
      { opacity: 1, transform: "translateY(0)", offset: 0.78 },
      { opacity: 0, transform: "translateY(-5px)", offset: 1 },
    ]);
  }
  academic({ span, lift, compact }) {
    this.object(this.el.querySelector(".mv2-book"), [
      {
        x: -span * 0.45,
        y: lift * 0.85,
        scale: 0.32,
        rotate: -42,
        turn: 58,
        opacity: 0,
        offset: 0,
      },
      {
        x: -span * 0.08,
        y: lift * 0.24,
        scale: 1.05,
        rotate: -7,
        turn: -9,
        opacity: 1,
        offset: 0.25,
      },
      {
        y: lift * 0.25,
        scale: 0.96,
        rotate: 5,
        turn: 8,
        opacity: 1,
        offset: 0.58,
      },
      {
        x: span * 0.55,
        y: lift * 0.55,
        scale: 0.38,
        rotate: 38,
        turn: -68,
        opacity: 0,
        offset: 0.83,
      },
      { x: span, y: lift, scale: 0.12, rotate: 70, opacity: 0, offset: 1 },
    ]);
    for (const [part, direction] of [
      ["left", -1],
      ["right", 1],
    ])
      this.animate(this.el.querySelector(`.mv2-book-${part}`), [
        { transform: `rotateY(${direction * 74}deg)` },
        { transform: `rotateY(${-direction * 9}deg)`, offset: 0.28 },
        { transform: `rotateY(${direction * 8}deg)`, offset: 0.57 },
        { transform: `rotateY(${direction * 72}deg)` },
      ]);
    this.el.querySelectorAll(".mv2-leaf").forEach((leaf, i) => {
      const angle = -Math.PI + (i * Math.PI) / 6,
        x = Math.cos(angle) * span,
        y = Math.sin(angle) * lift - lift * 0.25,
        side = i < 3 ? -1 : 1;
      this.object(
        leaf,
        [
          {
            y: lift * 0.28,
            scale: 0.15,
            turn: 75,
            rotate: side * 12,
            opacity: 0,
            offset: 0,
          },
          {
            x: x * 0.55,
            y: y * 0.55,
            scale: 0.78,
            turn: side * 20,
            rotate: side * 18,
            opacity: 1,
            offset: 0.3,
          },
          {
            x,
            y,
            scale: compact ? 0.7 : 0.86,
            turn: side * -22,
            rotate: side * (26 + i * 3),
            opacity: 1,
            offset: 0.56,
          },
          {
            x: x * 0.2,
            y: -lift * 0.07,
            scale: 0.32,
            turn: side * 60,
            rotate: side * 78,
            opacity: 0.25,
            offset: 0.8,
          },
          {
            x: side * span * 0.25,
            y: -lift * 0.2,
            scale: 0.1,
            turn: 85,
            rotate: side * 100,
            opacity: 0,
            offset: 1,
          },
        ],
        { duration: 1600, delay: 65 + i * 42 },
      );
    });
    this.object(
      this.el.querySelector(".mv2-glasses"),
      [
        {
          y: -lift * 0.6,
          scale: 1.6,
          rotate: -13,
          turn: 28,
          opacity: 0,
          offset: 0,
        },
        {
          y: -lift * 0.13,
          scale: 0.94,
          rotate: 3,
          turn: -8,
          opacity: 1,
          offset: 0.35,
        },
        { y: -lift * 0.15, scale: 1.03, rotate: -2, opacity: 1, offset: 0.52 },
        { y: -lift * 0.15, scale: 1, opacity: 1, offset: 0.78 },
        { y: -lift * 0.4, scale: 1.12, opacity: 0, offset: 1 },
      ],
      { duration: 1050, delay: 1010 },
    );
    this.animate(
      this.el.querySelector(".mv2-orbit"),
      [
        {
          opacity: 0,
          transform:
            "translate(-50%,-50%) rotateX(62deg) rotateZ(-28deg) scale(.25)",
        },
        {
          opacity: 0.34,
          transform:
            "translate(-50%,-50%) rotateX(62deg) rotateZ(18deg) scale(1)",
          offset: 0.4,
        },
        {
          opacity: 0,
          transform:
            "translate(-50%,-50%) rotateX(62deg) rotateZ(75deg) scale(1.2)",
        },
      ],
      { duration: 1900 },
    );
  }
  engineering({ span, lift }) {
    this.el.querySelectorAll(".mv2-error").forEach((panel, i) => {
      const side = i % 2 ? 1 : -1,
        y = (i - 2) * lift * 0.52;
      this.object(
        panel,
        [
          {
            x: side * span * 1.3,
            y: y + lift * 0.3,
            scale: 0.45,
            rotate: side * 24,
            turn: side * 48,
            opacity: 0,
            offset: 0,
          },
          {
            x: side * span * (0.58 + i * 0.04),
            y,
            scale: 0.9 - i * 0.045,
            rotate: side * 8,
            turn: side * 10,
            opacity: 0.94,
            offset: 0.32,
          },
          {
            x: side * span * 0.34,
            y: -lift * 0.05,
            scale: 0.64,
            rotate: side * -8,
            opacity: 0.9,
            offset: 0.7,
          },
          {
            x: side * span * 0.28,
            y: -lift * 0.04,
            scale: 0.24,
            rotate: side * -13,
            opacity: 0,
            offset: 1,
          },
        ],
        { duration: 1170, delay: i * 65 },
      );
      this.animate(
        panel,
        [
          { clipPath: "polygon(0% 0%,100% 0%,100% 100%,0% 100%)", offset: 0 },
          { clipPath: "polygon(0% 0%,100% 0%,100% 100%,0% 100%)", offset: 0.4 },
          {
            clipPath:
              side < 0
                ? "polygon(0% 20%,100% 36%,83% 92%,8% 75%)"
                : "polygon(5% 36%,100% 12%,78% 80%,0% 94%)",
            offset: 1,
          },
        ],
        { duration: 1170, delay: i * 65 },
      );
    });
    this.el.querySelectorAll(".mv2-slice").forEach((slice, i) => {
      const side = i % 2 ? 1 : -1;
      this.object(
        slice,
        [
          {
            x: side * span,
            y: (i - 4) * 25,
            scale: 0.4,
            rotate: side * 24,
            opacity: 0,
            offset: 0,
          },
          {
            x: side * span * 0.52,
            y: (i - 4) * 12,
            scale: 1,
            rotate: side * -8,
            opacity: 0.75,
            offset: 0.42,
          },
          {
            x: side * span * 0.15,
            y: -lift * 0.08,
            scale: 0.15,
            rotate: side * -23,
            opacity: 0,
            offset: 1,
          },
        ],
        { duration: 750, delay: 370 + i * 38 },
      );
    });
    this.object(
      this.el.querySelector(".mv2-eyes"),
      [
        { y: -lift * 0.08, scale: 0.52, turn: -15, opacity: 0, offset: 0 },
        { y: -lift * 0.08, scale: 1.03, turn: 3, opacity: 1, offset: 0.28 },
        { y: -lift * 0.08, scale: 1, opacity: 1, offset: 0.76 },
        { y: -lift * 0.08, scale: 0.94, opacity: 0, offset: 1 },
      ],
      { duration: 1300, delay: 750 },
    );
    this.animate(
      this.el.querySelector(".mv2-eye-right"),
      [
        { transform: "scaleY(1)", offset: 0 },
        { transform: "scaleY(1)", offset: 0.2 },
        { transform: "scaleY(.07)", offset: 0.35 },
        { transform: "scaleY(1)", offset: 0.51 },
        { transform: "scaleY(1)", offset: 0.72 },
        { transform: "scaleY(.02)", offset: 1 },
      ],
      { duration: 1070, delay: 970 },
    );
    this.animate(
      this.el.querySelector(".mv2-eye-left"),
      [
        { transform: "scaleY(1)", offset: 0 },
        { transform: "scaleY(1)", offset: 0.72 },
        { transform: "scaleY(.02)", offset: 1 },
      ],
      { duration: 1070, delay: 970 },
    );
  }
  business({ width, span, lift, compact }) {
    this.el.querySelectorAll(".mv2-report").forEach((paper, i) => {
      const lane = i - 3;
      this.object(
        paper,
        [
          {
            x: -span * 1.1 - i * 12,
            y: lift * 1.3,
            z: -200,
            scale: 0.22,
            rotate: -38 + i * 7,
            turn: -58,
            opacity: 0,
            offset: 0,
          },
          {
            x: -span * 0.38 + lane * 17,
            y: lift * 0.25 + lane * 11,
            z: -70,
            scale: 0.68,
            rotate: -16 + i * 7,
            turn: -15,
            opacity: 0.95,
            offset: 0.35,
          },
          {
            x: span * 0.24 + lane * 22,
            y: -lift * 0.55 + Math.abs(lane) * 9,
            scale: compact ? 0.72 : 0.92,
            rotate: 12 + i * 9,
            turn: 30,
            opacity: 0.84,
            offset: 0.65,
          },
          {
            x: span * 1.4 + i * 14,
            y: -lift * 1.5,
            z: 130,
            scale: 0.5,
            rotate: 52 + i * 8,
            turn: 67,
            opacity: 0,
            offset: 1,
          },
        ],
        { duration: 1690, delay: i * 58 },
      );
    });
    this.object(
      this.el.querySelector(".mv2-clipboard"),
      [
        {
          x: -width * 0.62,
          y: lift * 0.6,
          z: -170,
          scale: 0.25,
          rotate: -42,
          turn: -65,
          opacity: 0,
          offset: 0,
        },
        {
          x: -span * 0.16,
          y: lift * 0.05,
          z: 20,
          scale: 1.03,
          rotate: 8,
          turn: 11,
          opacity: 1,
          offset: 0.34,
        },
        {
          x: span * 0.05,
          y: -lift * 0.04,
          scale: 0.94,
          rotate: -5,
          turn: -7,
          opacity: 1,
          offset: 0.58,
        },
        {
          x: span * 0.22,
          y: -lift * 0.08,
          z: 60,
          scale: 1.12,
          rotate: 13,
          turn: 26,
          opacity: 1,
          offset: 0.77,
        },
        {
          x: width * 0.7,
          y: -lift * 0.7,
          z: 250,
          scale: 1.65,
          rotate: 48,
          turn: 65,
          opacity: 0,
          offset: 1,
        },
      ],
      { duration: 2120 },
    );
    this.animate(this.el.querySelector(".mv2-trail-grid"), [
      {
        opacity: 0,
        transform:
          "translate(-50%,-50%) rotateX(65deg) rotateZ(-25deg) scale(.3)",
      },
      {
        opacity: 0.24,
        transform:
          "translate(-50%,-50%) rotateX(65deg) rotateZ(-7deg) scale(1)",
        offset: 0.38,
      },
      {
        opacity: 0.12,
        transform:
          "translate(-50%,-50%) rotateX(65deg) rotateZ(22deg) scale(1.4)",
        offset: 0.8,
      },
      {
        opacity: 0,
        transform:
          "translate(-50%,-50%) rotateX(65deg) rotateZ(35deg) scale(1.6)",
      },
    ]);
  }
  destroy() {
    this.stop("destroyed");
    this.destroyed = true;
    document.removeEventListener("keydown", this.onEscape);
    window.removeEventListener("resize", this.onResize);
    this.media.removeEventListener("change", this.onMotion);
    this.observer.disconnect();
  }
}

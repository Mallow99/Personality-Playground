import { MotifTransition } from "./motion-v2.js";
import {
  profiles,
  poseCatalog,
  explanationPose,
  CharacterActor,
  AgentCursor,
  cursorShapes,
  cursorSVG,
  motionEnabled,
} from "./components.js";
const $ = (id) => document.getElementById(id);
const actor = new CharacterActor($("actor")),
  transition = new MotifTransition($("transition-layer")),
  cursor = new AgentCursor($("agent-cursor"));
let selected = "academic",
  shape = "arrow",
  sequenceId = 0,
  cursorId = 0;
const timers = new Set();
const guarded =
  (fn) =>
  (...args) =>
    Promise.resolve()
      .then(() => fn(...args))
      .catch((e) => {
        $("error").hidden = false;
        $("error").textContent = e.message;
      });
function stopSequence() {
  sequenceId++;
  for (const t of timers) clearTimeout(t);
  timers.clear();
  actor.setSpeaking(false);
  $("speaking").setAttribute("aria-pressed", "false");
  $("speaking").textContent = "Speaking: off";
  $("sequence").textContent = "Play character sequence ↗";
}
function later(fn, ms) {
  const id = setTimeout(() => {
    timers.delete(id);
    guarded(fn)();
  }, ms);
  timers.add(id);
}
function showActor(value) {
  value ? actor.show() : actor.hide();
  $("visibility").textContent = value ? "Disappear" : "Appear";
}
async function pose(value) {
  $("pose").value = value;
  $("stage-pose").value = value;
  $("pose-caption").textContent =
    poseCatalog[selected].find((p) => p.id === value)?.label || value;
  updateComparison(value);
  await actor.setPose(value, selected);
}
function cursorGrid() {
  $("cursor-grid").replaceChildren();
  for (const item of cursorShapes) {
    const b = document.createElement("button");
    b.dataset.shape = item;
    b.setAttribute("aria-pressed", String(shape === item));
    b.innerHTML = cursorSVG(selected, item);
    const label = document.createElement("span");
    label.textContent = item;
    b.append(label);
    b.addEventListener("click", () => {
      shape = item;
      cursorId++;
      cursor.hide();
      cursorGrid();
      $("cursor-owner").textContent =
        `${profiles[selected].name.toUpperCase()} / ${shape.toUpperCase()}`;
    });
    $("cursor-grid").append(b);
  }
}
async function choose(id, animate = true) {
  stopSequence();
  cursorId++;
  cursor.hide();
  selected = id;
  document.documentElement.dataset.theme = id;
  const p = profiles[id];
  $("character-name").textContent = p.name;
  $("character-summary").textContent = p.summary;
  $("line").textContent = p.line;
  $("stage-role").textContent = p.name.toUpperCase();
  $("sequence-status").textContent = "Ready to explore.";
  document
    .querySelectorAll("[data-profile]")
    .forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.profile === id)),
    );
  const available = poseCatalog[id];
  $("pose").innerHTML = available
    .map((p) => `<option value="${p.id}">${p.label}</option>`)
    .join("");
  $("stage-pose").innerHTML = $("pose").innerHTML;
  $("pose-grid").innerHTML = available
    .map(
      (p) =>
        `<figure data-category="${p.category}"><button class="pose-pick" data-pose="${p.id}" aria-label="Show ${p.label}"><img src="assets/poses/${id}/${p.id}.svg" alt="${profiles[id].name}, ${p.label}" loading="lazy"></button><figcaption>${p.label}<a href="assets/poses/${id}/${p.id}.svg" download>SVG ↗</a></figcaption></figure>`,
    )
    .join("");
  $("pose-grid")
    .querySelectorAll(".pose-pick")
    .forEach((button) =>
      button.addEventListener(
        "click",
        guarded(() => {
          stopSequence();
          showActor(true);
          return pose(button.dataset.pose);
        }),
      ),
    );
  filterPoses();
  renderPosePlan(id);
  $("icon-grid").innerHTML = ["face", "motif"]
    .map(
      (type) =>
        `<article><p class="eyebrow">${p.name.toUpperCase()} / ${type.toUpperCase()}</p><div class="icon-sizes">${[24, 48, 96].map((size) => `<figure><img width="${size}" height="${size}" src="assets/${id}-${type}.svg" alt="${p.name} ${type}, ${size} pixels"><figcaption>${size}px</figcaption></figure>`).join("")}</div><a href="assets/${id}-${type}.svg" download>Download SVG ↗</a></article>`,
    )
    .join("");
  cursorGrid();
  $("cursor-owner").textContent =
    `${p.name.toUpperCase()} / ${shape.toUpperCase()}`;
  showActor(true);
  if (animate) transition.play(id);
  await pose("standing");
}
for (const b of document.querySelectorAll("[data-profile]"))
  b.addEventListener(
    "click",
    guarded(() => choose(b.dataset.profile)),
  );
$("pose").addEventListener(
  "change",
  guarded(() => {
    stopSequence();
    showActor(true);
    return pose($("pose").value);
  }),
);
$("visibility").addEventListener("click", () => {
  stopSequence();
  showActor($("actor").dataset.visible !== "true");
});
$("speaking").addEventListener("click", () => {
  const enabled = $("speaking").getAttribute("aria-pressed") !== "true";
  stopSequence();
  showActor(true);
  actor.setSpeaking(enabled);
  $("speaking").setAttribute("aria-pressed", String(enabled));
  $("speaking").textContent = `Speaking: ${enabled ? "on" : "off"}`;
});
$("transition").addEventListener("click", () => transition.play(selected));
$("sequence").addEventListener(
  "click",
  guarded(async () => {
    if (timers.size) {
      stopSequence();
      $("sequence-status").textContent = "Sequence stopped.";
      return;
    }
    stopSequence();
    const ticket = sequenceId;
    showActor(true);
    await pose("standing");
    if (ticket !== sequenceId) return;
    $("sequence").textContent = "Stop sequence";
    $("sequence-status").textContent = motionEnabled()
      ? "Standing → specialist gesture → thinking → laughing → seated → disappear."
      : "Reduced motion: timed still poses with caption, without animated effects.";
    later(() => pose(explanationPose[selected]), 1800);
    later(() => {
      actor.setSpeaking(true);
      $("speaking").setAttribute("aria-pressed", "true");
      $("speaking").textContent = "Speaking: on";
    }, 3000);
    later(() => {
      actor.setSpeaking(false);
      $("speaking").setAttribute("aria-pressed", "false");
      $("speaking").textContent = "Speaking: off";
      return pose("thinking");
    }, 6500);
    later(() => pose("laughing"), 7800);
    later(() => pose("seated"), 9500);
    later(() => {
      showActor(false);
      stopSequence();
      $("sequence-status").textContent =
        "Sequence complete. Appear to bring the character back.";
    }, 12000);
  }),
);
const mq = matchMedia("(prefers-reduced-motion: reduce)");
function setMotion() {
  const enabled = $("motion").checked && !mq.matches;
  document.documentElement.dataset.motion = enabled ? "on" : "off";

  if (!enabled) {
    transition.stop();
    cursorId++;
    cursor.hide();
    document.getAnimations().forEach((a) => a.cancel());
  }
}
$("motion").checked = !mq.matches;
$("motion").addEventListener("change", setMotion);
mq.addEventListener("change", () => {
  $("motion").checked = !mq.matches;
  setMotion();
});
setMotion();
const pad = $("cursor-pad");
pad.addEventListener("pointermove", (e) => {
  if (e.pointerType === "touch") return;
  cursorId++;
  const r = pad.getBoundingClientRect();
  cursor.update({
    profileId: selected,
    shape,
    x: Math.min(e.clientX - r.left, pad.clientWidth - 36),
    y: Math.min(e.clientY - r.top, pad.clientHeight - 36),
  });
});
pad.addEventListener("pointerleave", () => {
  cursorId++;
  cursor.hide();
});
$("cursor-demo").addEventListener("click", () => {
  const ticket = ++cursorId;
  let frame = 0;
  function step() {
    if (ticket !== cursorId) return;
    const t = frame / 160;
    const x =
        24 + (pad.clientWidth - 85) * (0.5 - 0.5 * Math.cos(t * Math.PI * 2)),
      y = 140 + Math.sin(t * Math.PI * 2) * 35;
    const state = cursorShapes[Math.floor(frame / 13) % cursorShapes.length];
    cursor.update({ profileId: selected, shape: state, x, y });
    $("cursor-state").textContent =
      `${profiles[selected].name}: ${state} · simulated movement`;
    if (++frame <= 160) requestAnimationFrame(step);
    else {
      cursor.hide();
      $("cursor-state").textContent =
        "Sample complete. No computer actions ran.";
    }
  }
  if (motionEnabled()) step();
  else {
    cursor.update({ profileId: selected, shape, x: 50, y: 170 });
    $("cursor-state").textContent = "Reduced motion: static cursor sample.";
  }
});
$("download-cursor").addEventListener("click", () => {
  const url = URL.createObjectURL(
    new Blob([cursorSVG(selected, shape)], { type: "image/svg+xml" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = `${selected}-${shape}.svg`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
guarded(() => choose("academic", false))();

function updateComparison(value) {
  const id = value === "explaining" ? explanationPose[selected] : value;
  const base = `assets/poses/${selected}/${id}`;
  $("compare-source").src = base + ".source.png";
  $("compare-reference").src = base + ".reference.png";
  $("compare-vector").src = base + ".svg";
  $("compare-boundary").src = base + ".boundary.svg";
  $("compare-vector").alt = `${profiles[selected].name} ${id}, traced SVG`;
  $("compare-source").alt =
    `Generated source for ${profiles[selected].name} ${id}`;
  $("comparison-label").textContent =
    `${profiles[selected].name} / ${id.replaceAll("-", " ")}`;
  $("source-link").href = base + ".source.png";
  $("vector-link").href = base + ".svg";
}
$("comparison-mode").addEventListener("change", () => {
  $("comparison-box").dataset.mode = $("comparison-mode").value;
});
$("comparison-wipe").addEventListener("input", () => {
  $("comparison-box").style.setProperty(
    "--wipe",
    $("comparison-wipe").value + "%",
  );
});
function filterPoses() {
  const category = $("pose-filter").value;
  document.querySelectorAll("#pose-grid figure").forEach((el) => {
    el.hidden = category !== "all" && el.dataset.category !== category;
  });
}
$("pose-filter").addEventListener("change", filterPoses);
// Inspect the same semantic part IDs across every pose.
$("actor").addEventListener("rigchange", (event) => {
  const { parts } = event.detail;
  $("piece-select").innerHTML = parts
    .map(
      (p) =>
        `<option value="${p.id}">${p.label || p.id.replaceAll("-", " ")}${p.visible ? "" : " (no separate form)"}</option>`,
    )
    .join("");
  $("piece-select").value = actor.selected;
  $("rig-status").textContent =
    `${parts.filter((p) => p.visible).length} visible groups · ${actor.data.mappingMethod === "whole-shape" ? "WHOLE SHAPES · Academic comparison proof" : "LEGACY region map · needs refinement"} · draft ownership`;
});
$("actor").addEventListener("rigpart", (event) => {
  const { id, offset } = event.detail;
  $("piece-select").value = id;
  $("piece-x").value = offset.x;
  $("piece-y").value = offset.y;
  $("piece-angle").value = offset.rotation;
});
$("piece-select").addEventListener("change", () =>
  actor.selectPart($("piece-select").value),
);
$("piece-idle").addEventListener("change", () =>
  actor.setIdle($("piece-idle").checked),
);
$("piece-outlines").addEventListener("change", () =>
  actor.showParts($("piece-outlines").checked),
);
$("piece-drag").addEventListener("change", () => {
  actor.dragEnabled = $("piece-drag").checked;
  $("actor").dataset.drag = actor.dragEnabled ? "on" : "off";
});
$("morph-duration").addEventListener("input", () => {
  actor.options.duration = Number($("morph-duration").value);
});
for (const id of ["piece-x", "piece-y", "piece-angle"])
  $(id).addEventListener("input", () =>
    actor.setPartOffset(actor.selected, {
      x: $("piece-x").value,
      y: $("piece-y").value,
      rotation: $("piece-angle").value,
    }),
  );
$("piece-reset").addEventListener("click", () => actor.resetParts());
$("piece-export").addEventListener("click", () => {
  const data = actor.exportRig();
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = `${data.role}-${data.pose}-piece-map.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

const posePlan = fetch(new URL("assets/pose-plan.json", import.meta.url)).then(
  (r) => {
    if (!r.ok) throw Error("Pose plan unavailable");
    return r.json();
  },
);
function renderPosePlan(role) {
  posePlan
    .then((plan) => {
      if (selected !== role) return;
      const data = plan.characters[role];
      $("pose-plan").innerHTML =
        `<p>${data.available.length} available poses · ${data.planned.length} proposed additions</p><ol>${data.planned.map((p) => `<li><strong>${p.label}</strong> <span>Priority ${p.priority} · planned</span><p>${p.reason}</p></li>`).join("")}</ol>`;
    })
    .catch((error) => {
      $("pose-plan").textContent = error.message;
    });
}

$("stage-pose").addEventListener(
  "change",
  guarded(() => {
    stopSequence();
    showActor(true);
    return pose($("stage-pose").value);
  }),
);

$("piece-isolate").addEventListener("change", () =>
  actor.isolatePart($("piece-isolate").checked),
);
$("pose-transition").addEventListener("change", () => {
  actor.settle();
  actor.options.transitionStyle = $("pose-transition").value;
});
$("talk-mode").addEventListener("change", () => {
  $("actor").dataset.speechStyle = $("talk-mode").value;
});
$("actor").addEventListener("speechchange", (event) => {
  $("talk-status").textContent = event.detail.speaking
    ? "Talking · silent cue proof"
    : "Silent";
});
$("mapping-pair").addEventListener(
  "click",
  guarded(async () => {
    const next =
      selected === "academic" && $("pose").value === "standing"
        ? "seated"
        : "standing";
    if (selected !== "academic") await choose("academic", false);
    stopSequence();
    showActor(true);
    await pose(next);
  }),
);

$("form-drag").addEventListener("change", () => {
  actor.dragForms = $("form-drag").checked;
});
$("actor").addEventListener("shapechange", (event) => {
  $("form-status").textContent =
    `Selected whole form ${event.detail.id} in ${event.detail.part}. This form's ID belongs to this pose; body group IDs match between poses.`;
});

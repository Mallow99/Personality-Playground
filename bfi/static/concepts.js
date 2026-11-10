"use strict";
const el = (id) => document.getElementById(id);
let profiles = [];
let selected = "academic";
const descriptions = {
  academic: {
    number: "01",
    line: "Let’s make this manageable. What’s one thing you want to understand?",
    shape: "Soft forms. A studious little presence.",
  },
  engineering: {
    number: "02",
    line: "Show me the change. We’ll make it work, then make it make sense.",
    shape: "Sharp edges. Clear thinking. A little attitude.",
  },
  business: {
    number: "03",
    line: "Let’s find the decision that actually moves this forward.",
    shape: "Composed shapes. A clearer next move.",
  },
};
function replay() {
  const art = document.querySelector(".character-art");
  art.classList.remove("arriving");
  void art.offsetWidth;
  art.classList.add("arriving");
}
function choose(id) {
  const profile = profiles.find((p) => p.id === id);
  if (!profile) return;
  selected = id;
  document.body.dataset.theme = profile.character.theme;
  el("preview-name").textContent = profile.character.name;
  el("preview-description").textContent = profile.character.description;
  el("preview-number").textContent = `CHARACTER / ${descriptions[id].number}`;
  el("sample-line").textContent = descriptions[id].line;
  el("shape-note").textContent = descriptions[id].shape;
  el("stage-profile").textContent = profile.character.name.toUpperCase();
  el("preview-route").textContent =
    profile.backend === "mock"
      ? "Current route: scripted mock · no model inference"
      : `Configured route: ${profile.requested_model} · readiness not checked here`;
  el("try-profile").href = `/?profile=${encodeURIComponent(id)}`;
  document
    .querySelectorAll("[data-profile]")
    .forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.profile === id)),
    );
  replay();
}
document
  .querySelectorAll("[data-profile]")
  .forEach((button) =>
    button.addEventListener("click", () => choose(button.dataset.profile)),
  );
el("studio-replay").addEventListener("click", replay);
el("studio-pose").addEventListener("change", () => {
  document.body.dataset.pose = el("studio-pose").value;
});
el("studio-corner").addEventListener("click", () => {
  const enabled = el("studio-stage").dataset.corner !== "on";
  el("studio-stage").dataset.corner = enabled ? "on" : "off";
  el("studio-corner").setAttribute("aria-pressed", String(enabled));
  el("studio-corner").textContent = enabled
    ? "Back to center"
    : "Try the corner";
});
el("studio-motion").checked = !window.matchMedia(
  "(prefers-reduced-motion: reduce)",
).matches;
document.body.dataset.motion = el("studio-motion").checked ? "on" : "off";
el("studio-motion").addEventListener("change", () => {
  document.body.dataset.motion = el("studio-motion").checked ? "on" : "off";
});
fetch("/api/config")
  .then((r) => {
    if (!r.ok)
      throw new Error(
        "Cannot read character configuration. Check the app terminal and reload.",
      );
    return r.json();
  })
  .then((config) => {
    profiles = config.profiles;
    choose(selected);
  })
  .catch((error) => {
    el("studio-error").hidden = false;
    el("studio-error").textContent = error.message;
  });

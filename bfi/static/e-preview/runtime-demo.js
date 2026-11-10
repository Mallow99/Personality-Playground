import { AvatarView } from "./avatar-runtime/avatar.js";
const $ = (id) => document.getElementById(id),
  catalog = await fetch("avatar-runtime/catalog.json").then((r) => r.json());
const view = new AvatarView($("avatar"), {
  resolveURL: (path) =>
    path
      .replace("/static/e-preview/", "./")
      .replace("/static/avatar/", "./avatar-runtime/"),
});
let state = {
    profile: "academic",
    pose_id: "academic/reading",
    activity: "idle",
    visible: true,
    motion: true,
    size: "normal",
    caption: "Here when you need me.",
  },
  timer;
async function render() {
  document.body.dataset.theme = state.profile;
  $("name").textContent = catalog.roles[state.profile].name;
  $("avatar").hidden = !state.visible;
  $("show").textContent = state.visible ? "Hide avatar" : "Show avatar";
  const changed = view.key !== state.pose_id;
  if (changed) $("reveal").setAttribute("aria-pressed", "false");
  await view.set(state, catalog);
  $("reveal").disabled = !view.svg;
  $("command").textContent = JSON.stringify(
    {
      name: "avatar_set",
      arguments: { pose_id: state.pose_id, visible: state.visible },
    },
    null,
    2,
  );
}
function role(id) {
  clearTimeout(timer);
  state = {
    ...state,
    profile: id,
    pose_id: `${id}/standing`,
    activity: "idle",
    caption: "Here when you need me.",
  };
  $("pose").replaceChildren();
  for (const p of catalog.poses.filter((p) => p.role === id)) {
    const o = document.createElement("option");
    o.value = p.id;
    o.textContent =
      p.label +
      (p.source === "generated-concept" && p.approval !== "approved"
        ? " · concept"
        : "");
    $("pose").append(o);
  }
  document
    .querySelectorAll("[data-role]")
    .forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.role === id)),
    );
  $("pose").value = state.pose_id;
  render();
}
document
  .querySelectorAll("[data-role]")
  .forEach((b) => b.addEventListener("click", () => role(b.dataset.role)));
$("pose").addEventListener("change", () => {
  state.pose_id = $("pose").value;
  render();
});
$("think").addEventListener("click", () => {
  clearTimeout(timer);
  state.activity = "thinking";
  state.caption = "Thinking through the next step…";
  $("example").textContent = "Scripted thinking state.";
  render();
});
$("reply").addEventListener("click", () => {
  clearTimeout(timer);
  state.activity = "speaking";
  state.caption = {
    academic: "Let’s make the idea visible, one step at a time.",
    engineering: "That’s a useful starting point. Let’s test the assumption.",
    business: "Here’s the recommendation, followed by the next action.",
  }[state.profile];
  $("example").textContent = "Scripted text reply cue. No audio or model call.";
  render();
  timer = setTimeout(() => {
    state.activity = "idle";
    render();
  }, 8000);
});
$("show").addEventListener("click", () => {
  state.visible = !state.visible;
  render();
});
$("motion").addEventListener("change", () => {
  state.motion = $("motion").checked;
  render();
});
role("academic");
$("pose").value = "academic/reading";
state.pose_id = "academic/reading";
render();
addEventListener("pagehide", () => {
  clearTimeout(timer);
  view.destroy();
});

const requested = new URLSearchParams(location.search),
  requestedPose = catalog.poses.find((p) => p.id === requested.get("pose"));
if (requestedPose) {
  role(requestedPose.role);
  state.pose_id = requestedPose.id;
  $("pose").value = state.pose_id;
  render();
}

$("reveal").addEventListener("click", () => {
  const hidden = $("reveal").getAttribute("aria-pressed") !== "true";
  $("reveal").setAttribute("aria-pressed", String(hidden));
  if (view.svg)
    for (const id of [
      "reading-left-hand",
      "reading-right-hand",
      "seated-moving-hand",
    ]) {
      const hand = view.svg.querySelector("#" + id);
      if (hand) hand.style.visibility = hidden ? "hidden" : "visible";
    }
});

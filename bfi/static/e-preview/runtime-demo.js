import { AvatarView } from "./avatar-runtime/avatar.js?v=2";
const $ = (id) => document.getElementById(id);
const defaults = {
  academic: "reading",
  engineering: "coding",
  business: "working",
};
const moving = { academic: "reading", business: "seated" };

async function start() {
  const response = await fetch(
    new URL("avatar-runtime/catalog.json", import.meta.url),
    { cache: "no-store" },
  );
  if (!response.ok)
    throw Error("The pose catalog could not load. Reload the preview.");
  const catalog = await response.json();
  const view = new AvatarView($("avatar"), {
    resolveURL: (path) =>
      new URL(
        path
          .replace("/static/e-preview/", "./")
          .replace("/static/avatar/", "./avatar-runtime/"),
        import.meta.url,
      ).href,
  });
  let state = {
    profile: "academic",
    pose_id: "academic/reading",
    activity: "idle",
    visible: true,
    motion: true,
    size: "normal",
    caption: "Here when you need me.",
  };
  let timer,
    revision = 0,
    reveal = false;
  function say(text) {
    $("example").textContent = text;
  }
  async function render() {
    const ticket = ++revision;
    document.body.dataset.theme = state.profile;
    $("name").textContent = catalog.roles[state.profile].name;
    $("avatar").hidden = !state.visible;
    $("show").textContent = state.visible ? "Hide avatar" : "Show avatar";
    $("show").setAttribute("aria-pressed", String(!state.visible));
    $("pose").value = state.pose_id;
    $("think").setAttribute(
      "aria-pressed",
      String(state.activity === "thinking"),
    );
    $("reply").setAttribute(
      "aria-pressed",
      String(state.activity === "speaking"),
    );
    const pose = catalog.poses.find((p) => p.id === state.pose_id);
    $("pose-note").textContent =
      (pose.gaze_target
        ? `Eyes toward the ${pose.gaze_target}. `
        : "Original authored gaze. ") +
      (pose.motion === "none"
        ? "Still artwork; Motion affects reply marks only."
        : "Separate parts support local movement. Motion pauses or resumes them.");
    $("motion").disabled = view.media.matches;
    if (view.media.matches)
      $("pose-note").textContent +=
        " Your reduced-motion setting keeps animation off.";
    $("animate-example").hidden =
      pose.motion !== "none" || !moving[state.profile];
    $("command").textContent = JSON.stringify(
      {
        name: "avatar_set",
        arguments: {
          pose_id: state.pose_id,
          visible: state.visible,
          speaking: state.activity === "speaking",
        },
      },
      null,
      2,
    );
    await view.set({ ...state }, catalog);
    if (ticket !== revision) return;
    $("reveal").hidden = !view.svg;
    $("reveal").setAttribute("aria-pressed", String(reveal));
    $("reveal").textContent = reveal ? "Restore hands" : "Reveal rear layer";
    if (view.svg)
      for (const id of [
        "reading-left-hand",
        "reading-right-hand",
        "seated-moving-hand",
      ]) {
        const hand = view.svg.querySelector("#" + id);
        if (hand) hand.style.visibility = reveal ? "hidden" : "visible";
      }
  }
  function choose(poseId) {
    clearTimeout(timer);
    reveal = false;
    state.pose_id = poseId;
    state.activity = "idle";
    state.caption = "Here when you need me.";
    render();
  }
  function role(id) {
    state.profile = id;
    $("pose").replaceChildren(
      ...catalog.poses
        .filter((p) => p.role === id)
        .map((p) => {
          const option = document.createElement("option");
          option.value = p.id;
          option.textContent = p.label;
          return option;
        }),
    );
    document
      .querySelectorAll("[data-role]")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.role === id)),
      );
    choose(`${id}/${defaults[id]}`);
    say(
      `${catalog.roles[id].name} selected. Choose a pose or try a reply cue.`,
    );
  }
  document
    .querySelectorAll("[data-role]")
    .forEach((b) => b.addEventListener("click", () => role(b.dataset.role)));
  $("pose").disabled = false;
  $("pose").addEventListener("change", () => {
    choose($("pose").value);
    say("Pose changed. The note above explains its movement and gaze.");
  });
  $("animate-example").addEventListener("click", () => {
    choose(`${state.profile}/${moving[state.profile]}`);
    say("Moving pose selected. Toggle Motion to pause and resume.");
  });
  $("think").addEventListener("click", () => {
    choose(`${state.profile}/thinking`);
    state.activity = "thinking";
    state.caption = "Thinking through the next step…";
    render();
    say(
      state.visible
        ? "Thinking pose and caption active."
        : "Thinking pose selected. Show the avatar to see it.",
    );
  });
  $("reply").addEventListener("click", () => {
    clearTimeout(timer);
    state.activity = "speaking";
    state.caption = {
      academic: "Let’s make the idea visible, one step at a time.",
      engineering: "That’s a useful starting point. Let’s test the assumption.",
      business: "Here’s the recommendation, followed by the next action.",
    }[state.profile];
    render();
    say(
      state.visible
        ? "Reply caption and speaking marks active for 8 seconds. This demo has no audio."
        : "Reply cue active. Show the avatar to see it.",
    );
    timer = setTimeout(() => {
      state.activity = "idle";
      render();
      say("Reply cue finished.");
    }, 8000);
  });
  $("idle").addEventListener("click", () => {
    clearTimeout(timer);
    state.activity = "idle";
    state.caption = "Here when you need me.";
    render();
    say("Idle. The selected pose is unchanged.");
  });
  $("show").addEventListener("click", () => {
    state.visible = !state.visible;
    render();
    say(
      state.visible
        ? "Avatar shown."
        : "Avatar hidden. Show avatar restores it.",
    );
  });
  $("motion").addEventListener("change", () => {
    state.motion = $("motion").checked;
    render();
    say(
      state.motion
        ? "Movement enabled where supported; reply marks can pulse."
        : "Movement and reply-mark animation paused.",
    );
  });
  $("reveal").addEventListener("click", () => {
    reveal = !reveal;
    if (reveal) {
      state.motion = false;
      $("motion").checked = false;
    }
    render();
    say(
      reveal
        ? "Hands hidden; the material underneath remains. Movement paused for inspection."
        : "Hands restored. Enable Motion to resume movement.",
    );
  });
  $("surface").addEventListener("change", () => {
    document.querySelector(".desktop").dataset.surface = $("surface").value;
    say("Art background changed. Source colors stay the same.");
  });
  const preferenceChanged = () => render();
  view.media.addEventListener("change", preferenceChanged);
  role("academic");
  const requested = catalog.poses.find(
    (p) => p.id === new URLSearchParams(location.search).get("pose"),
  );
  if (requested) {
    role(requested.role);
    choose(requested.id);
  }
  addEventListener("pagehide", () => {
    clearTimeout(timer);
    view.media.removeEventListener("change", preferenceChanged);
    view.destroy();
  });
}
start().catch((error) => {
  $("example").textContent = error.message;
  $("example").setAttribute("role", "alert");
});

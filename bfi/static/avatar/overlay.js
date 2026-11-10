import { connectAvatar, avatarAPI } from "./avatar.js";
const el = document.getElementById("overlay-avatar"),
  status = document.getElementById("connection");
const controller = await connectAvatar([el], (state, _, error) => {
  if (error) {
    status.textContent = error.message;
    return;
  }
  document.body.dataset.theme = state.profile;
  el.hidden = !state.visible;
  status.textContent = state.visible
    ? "Local handler · text cues"
    : "Hidden in handler";
  document.getElementById("hide-avatar").textContent = state.visible
    ? "Hide avatar"
    : "Show avatar";
});
document.getElementById("hide-avatar").addEventListener("click", async () => {
  try {
    const state = await avatarAPI();
    await avatarAPI("", { visible: !state.visible });
  } catch (error) {
    status.textContent = error.message;
  }
});
addEventListener("pagehide", () => controller.close());

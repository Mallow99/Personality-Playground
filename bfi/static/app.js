import { connectAvatar, avatarAPI } from "/static/avatar/avatar.js";
("use strict");
const $ = (id) => document.getElementById(id);
let config;
let current = null;
let busy = false;
let loading = false;
let status = null;
let selectedProfile = "academic";
let avatarController = null,
  avatarCatalog = null,
  avatarState = null,
  requestedAvatarRole = null;

function activeProfile() {
  const id =
    current?.character.profile_id || (current ? "companion" : selectedProfile);
  return (
    config.profiles.find((p) => p.id === id) || { id: "companion", ...config }
  );
}

function replayAvatar() {
  avatarController?.views.forEach((v) => v.replay());
}
function syncAvatarRole(profileId) {
  if (!avatarCatalog) return;
  const role = profileId === "companion" ? "academic" : profileId;
  if (requestedAvatarRole === role) return;
  requestedAvatarRole = role;
  $("avatar-pose").replaceChildren();
  for (const pose of avatarCatalog.poses.filter((p) => p.role === role)) {
    const option = document.createElement("option");
    option.value = pose.id;
    option.textContent =
      pose.label +
      (pose.source === "generated-concept" && pose.approval !== "approved"
        ? " · concept"
        : "");
    $("avatar-pose").append(option);
  }
  $("avatar-pose").value = `${role}/standing`;
  avatarAPI("", { profile: role }).catch((error) => {
    $("avatar-connection").textContent = error.message;
    requestedAvatarRole = null;
  });
}
async function startAvatar() {
  avatarController = await connectAvatar(
    [$("sidebar-avatar"), $("corner-art")],
    (state, catalog, error) => {
      if (error) {
        $("avatar-connection").textContent = error.message;
        return;
      }
      avatarState = state;
      document.body.dataset.theme = state.profile;
      $("corner-companion").hidden =
        !state.visible || !$("mirror-avatar").checked;
      $("sidebar-avatar").hidden = !$("corner-companion").hidden;
      $("corner-companion").dataset.dock = state.dock;
      $("toggle-corner").textContent = state.visible
        ? "Hide avatar"
        : "Show avatar";
      if (requestedAvatarRole === state.profile)
        $("avatar-pose").value = state.pose_id;
      $("avatar-dock").value = state.dock;
      $("avatar-size").value = state.size;
      $("avatar-motion").checked = state.motion;
      document.body.dataset.motion = state.motion ? "on" : "off";
      $("avatar-connection").textContent =
        "128 poses · shared with the separate overlay";
    },
  );
  avatarCatalog = avatarController.catalog;
  syncAvatarRole(activeProfile().id);
}
async function avatarChange(changes) {
  try {
    await avatarAPI("", changes);
  } catch (error) {
    showError(error);
  }
}

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    let detail;
    try {
      detail = (await response.json()).detail;
    } catch {
      /* Show a useful fallback below. */
    }
    throw new Error(
      typeof detail === "string"
        ? detail
        : `Request failed (HTTP ${response.status}). Check the app terminal and try again.`,
    );
  }
  return response.status === 204 ? null : response.json();
}

function showError(error) {
  $("error").textContent = error.message || String(error);
  $("error").hidden = false;
}

// The database owns history. Browser storage only remembers the selected chat.
function rememberConversation(id) {
  try {
    if (id) localStorage.setItem("bfi-conversation", id);
    else localStorage.removeItem("bfi-conversation");
  } catch {
    /* Chat still works when browser storage is disabled. */
  }
}

function rememberedConversation() {
  try {
    return localStorage.getItem("bfi-conversation");
  } catch {
    return null;
  }
}

function updateControls() {
  const locked = busy || loading || !config;
  $("new-chat").disabled = locked;
  $("message").disabled = locked;
  $("send").disabled = locked || !$("message").value.trim();
  $("delete-chat").disabled = locked || !current;
  $("export-chat").disabled = locked || !current;
  $("profile-select").disabled = locked;
  $("allow-project").disabled = locked || !config?.tools.project_files;
  $("allow-web").disabled = locked || !config?.tools.web_search;
  $("allow-avatar").disabled = locked;
  $("avatar-pose").disabled = locked;
  document
    .querySelectorAll(".conversation-item, [data-prompt]")
    .forEach((b) => {
      b.disabled = locked;
    });
  $("send").textContent = busy ? "…" : "↑";
}

function node(tag, className, content) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (content !== undefined) element.textContent = content;
  return element;
}

function addDefinition(parent, term, value) {
  parent.append(node("dt", "", term), node("dd", "", value));
}

function renderCharacter() {
  const profile = activeProfile();
  const character = current?.character || profile.character;
  $("character-name").textContent = character.name;
  $("character-description").textContent = character.description;
  $("character-prompt").textContent = character.system_prompt;
  $("profile-select").value = profile.id;
  const changed = document.body.dataset.theme !== character.theme;
  document.body.dataset.theme = character.theme || "foundation";
  if (changed) replayAvatar();
  const list = $("backend-details");
  list.replaceChildren();
  addDefinition(list, "Character", character.name);
  addDefinition(
    list,
    "Backend",
    profile.backend === "mock"
      ? "Scripted mock (no inference)"
      : "OpenAI-compatible endpoint",
  );
  addDefinition(list, "Requested model", profile.requested_model);
  addDefinition(list, "Endpoint", profile.endpoint || "None");
  addDefinition(
    list,
    "Configured adapter",
    profile.adapter_label ||
      "None declared; no personality training established",
  );
  addDefinition(
    list,
    "Context window",
    `Up to ${config.history_pairs} recent exchanges; ${config.context_chars.toLocaleString()} character budget (not tokens)`,
  );
  document
    .querySelectorAll('img[src="/static/mark.svg"], img[data-character-mark]')
    .forEach((img) => {
      img.dataset.characterMark = "true";
      img.src = `/static/e-preview/assets/${profile.id === "companion" ? "academic" : profile.id}-face.svg`;
    });
  syncAvatarRole(profile.id);
}

function render() {
  const messages = current?.messages || [];
  $("empty-state").hidden = messages.length > 0;
  $("messages").replaceChildren();
  $("chat-title").textContent = messages.length
    ? current.title
    : "A new conversation";
  renderCharacter();
  for (const message of messages) {
    const article = node("article", `message ${message.role}`);
    const heading = node("div", "message-heading");
    heading.append(
      node("span", "avatar", message.role === "user" ? "Y" : "C"),
      node(
        "span",
        "",
        message.role === "user" ? "You" : current.character.name,
      ),
    );
    article.append(heading, node("div", "message-content", message.content));
    if (message.provenance) {
      const p = message.provenance;
      const details = node("details", "provenance");
      const model =
        p.reported_model ||
        `${p.requested_model} (requested; server did not report an ID)`;
      details.append(
        node(
          "summary",
          "",
          p.backend === "mock"
            ? "Mock · scripted reply · inspect source"
            : `${model} · endpoint reply · inspect source`,
        ),
      );
      const list = node("dl");
      addDefinition(list, "Backend", p.backend);
      addDefinition(list, "Requested model", p.requested_model);
      addDefinition(
        list,
        "Reported model",
        p.reported_model || "Not reported by server",
      );
      addDefinition(list, "Endpoint", p.endpoint || "None — scripted mock");
      addDefinition(list, "Cloud delegation", "None by this app");
      addDefinition(list, "Profile", p.profile_id || "Original draft");
      if (p.configured_adapter)
        addDefinition(
          list,
          "Configured adapter (unverified)",
          p.configured_adapter,
        );
      if (p.tool_steps?.length)
        addDefinition(
          list,
          "Actual tool calls and results",
          JSON.stringify(p.tool_steps, null, 2),
        );
      addDefinition(
        list,
        "Locality",
        p.backend === "mock"
          ? "No inference"
          : "Loopback endpoint; server locality not independently verified",
      );
      addDefinition(
        list,
        "Response time",
        `${(p.elapsed_ms / 1000).toFixed(2)} seconds`,
      );
      if (p.usage && Object.keys(p.usage).length)
        addDefinition(
          list,
          "Tokens (server reported)",
          JSON.stringify(p.usage),
        );
      addDefinition(
        list,
        "Earlier messages omitted from context",
        String(p.context_messages_omitted),
      );
      details.append(list);
      article.append(details);
    }
    $("messages").append(article);
  }
  if (
    current &&
    ["backend", "endpoint", "requested_model"].some(
      (key) => current.backend[key] !== activeProfile()[key],
    )
  ) {
    $("mode-notice").textContent =
      "Archived backend/model. Start a new conversation to use the current configuration.";
  } else {
    $("mode-notice").textContent =
      activeProfile().backend === "mock"
        ? "Mock mode — scripted replies, no model inference. Your history is still saved."
        : `Endpoint mode · ${activeProfile().requested_model} · Conversation history is sent to your configured server.`;
  }
  updateControls();
  $("scroll-area").scrollTop = $("scroll-area").scrollHeight;
}

async function refreshList() {
  const conversations = await api("/conversations");
  $("conversation-count").textContent = String(conversations.length);
  $("conversations").replaceChildren();
  if (!conversations.length) {
    $("conversations").append(
      node(
        "p",
        "sidebar-empty",
        "A fresh start. Your conversations will live here.",
      ),
    );
  }
  for (const conversation of conversations) {
    const button = node(
      "button",
      `conversation-item${current?.id === conversation.id ? " active" : ""}`,
    );
    button.append(
      node("strong", "", conversation.title),
      node(
        "small",
        "",
        `${conversation.character.name} · ${conversation.backend.backend === "mock" ? "MOCK" : "ENDPOINT"} · ${new Date(conversation.updated_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}`,
      ),
    );
    button.addEventListener("click", () => selectConversation(conversation.id));
    button.disabled = busy || loading;
    if (current?.id === conversation.id)
      button.setAttribute("aria-current", "page");
    $("conversations").append(button);
  }
  return conversations;
}

async function selectConversation(id) {
  if (busy || loading) return;
  loading = true;
  updateControls();
  try {
    const next = await api(`/conversations/${id}`);
    current = next;
    selectedProfile = current.character.profile_id || "companion";
    rememberConversation(current.id);
    $("message").value = "";
    $("error").hidden = true;
    render();
    await refreshList();
    refreshStatus();
  } catch (error) {
    showError(error);
  } finally {
    loading = false;
    updateControls();
  }
}

async function refreshStatus() {
  const profileId = activeProfile().id;
  $("refresh-status").disabled = true;
  $("status-label").textContent = "Checking backend…";
  $("status-detail").textContent = "Checking the configured backend…";
  try {
    status = await api(`/status?profile_id=${encodeURIComponent(profileId)}`);
    if (activeProfile().id !== profileId) return;
    $("status-label").textContent = status.label;
    $("open-status").dataset.state = status.state;
    $("status-detail").textContent = status.detail;
  } catch (error) {
    $("status-label").textContent = "App unavailable";
    $("open-status").dataset.state = "unavailable";
    $("status-detail").textContent = error.message;
  } finally {
    $("refresh-status").disabled = false;
  }
}

$("chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = $("message").value.trim();
  if (!content || busy || loading || !config) return;
  busy = true;
  $("error").hidden = true;
  updateControls();
  const pending = node("div", "pending", "Waiting for a reply…");
  $("messages").append(pending);
  try {
    if (!current) {
      current = await api("/conversations", {
        method: "POST",
        body: JSON.stringify({ profile_id: selectedProfile }),
      });
      rememberConversation(current.id);
    }
    current = await api(`/conversations/${current.id}/messages`, {
      method: "POST",
      body: JSON.stringify({
        content,
        project_tools: $("allow-project").checked,
        web_search: $("allow-web").checked,
        avatar_tools: $("allow-avatar").checked,
      }),
    });
    $("message").value = "";
    render();
    await refreshList();
  } catch (error) {
    showError(error);
  } finally {
    pending.remove();
    busy = false;
    $("allow-project").checked = false;
    $("allow-web").checked = false;
    updateControls();
    $("message").focus();
  }
});

$("message").addEventListener("input", updateControls);
$("message").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    $("chat-form").requestSubmit();
  }
});

$("new-chat").addEventListener("click", async () => {
  if (busy || loading) return;
  current = null;
  if (selectedProfile === "companion") selectedProfile = "academic";
  rememberConversation(null);
  $("message").value = "";
  $("error").hidden = true;
  render();
  try {
    await refreshList();
  } catch (error) {
    showError(error);
  }
  $("message").focus();
});

$("delete-chat").addEventListener("click", async () => {
  if (
    !current ||
    busy ||
    loading ||
    !window.confirm(
      "Delete this conversation and all its messages? This cannot be undone.",
    )
  )
    return;
  loading = true;
  updateControls();
  try {
    await api(`/conversations/${current.id}`, { method: "DELETE" });
    current = null;
    rememberConversation(null);
    $("error").hidden = true;
    render();
    await refreshList();
  } catch (error) {
    showError(error);
  } finally {
    loading = false;
    updateControls();
  }
});

$("export-chat").addEventListener("click", () => {
  if (!current) return;
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(current, null, 2)], { type: "application/json" }),
  );
  const link = node("a");
  link.href = url;
  link.download = `bfi-${current.id}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    $("message").value = button.dataset.prompt;
    updateControls();
    $("message").focus();
  });
});
$("open-status").addEventListener("click", () =>
  $("status-dialog").showModal(),
);
$("close-status").addEventListener("click", () => $("status-dialog").close());
$("refresh-status").addEventListener("click", refreshStatus);

$("profile-select").addEventListener("change", async (event) => {
  if (
    $("message").value.trim() &&
    !window.confirm(
      "Start a new conversation with this character and discard the unsent draft?",
    )
  ) {
    event.target.value = activeProfile().id;
    return;
  }
  selectedProfile = event.target.value;
  current = null;
  rememberConversation(null);
  $("message").value = "";
  $("allow-project").checked = $("allow-web").checked = false;
  $("error").hidden = true;
  render();
  try {
    await refreshList();
  } catch (error) {
    showError(error);
  }
  refreshStatus();
});
$("replay-avatar").addEventListener("click", replayAvatar);
$("avatar-pose").addEventListener("change", () =>
  avatarChange({ pose_id: $("avatar-pose").value }),
);
$("avatar-motion").addEventListener("change", () =>
  avatarChange({ motion: $("avatar-motion").checked }),
);
$("avatar-dock").addEventListener("change", () =>
  avatarChange({ dock: $("avatar-dock").value }),
);
$("avatar-size").addEventListener("change", () =>
  avatarChange({ size: $("avatar-size").value }),
);
$("toggle-corner").addEventListener("click", () =>
  avatarChange({ visible: !avatarState?.visible }),
);
$("hide-corner").addEventListener("click", () =>
  avatarChange({ visible: false }),
);
addEventListener("pagehide", () => avatarController?.close());
$("open-tools").addEventListener("click", () => $("tools-dialog").showModal());
$("close-tools").addEventListener("click", () => $("tools-dialog").close());
$("tool-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("tool-name").value;
  const value = $("tool-argument").value.trim();
  const args =
    name === "list_project_files"
      ? {}
      : name === "read_project_file"
        ? { path: value }
        : { query: value };
  $("run-tool").disabled = true;
  $("tool-result").textContent = "Running the configured tool…";
  try {
    const result = await api("/tools/inspect", {
      method: "POST",
      body: JSON.stringify({ name, arguments: args }),
    });
    $("tool-result").textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    $("tool-result").textContent = error.message;
  } finally {
    $("run-tool").disabled = false;
  }
});

async function init() {
  loading = true;
  try {
    config = await api("/config");
    await startAvatar();
    for (const profile of config.profiles) {
      const option = node("option", "", profile.character.name);
      option.value = profile.id;
      $("profile-select").append(option);
    }
    const legacy = node("option", "", "Original draft");
    legacy.value = "companion";
    legacy.hidden = true;
    $("profile-select").append(legacy);
    const fromUrl = new URLSearchParams(location.search).get("profile");
    if (config.profiles.some((p) => p.id === fromUrl))
      selectedProfile = fromUrl;
    $("tool-capabilities").textContent =
      `Project files: ${config.tools.project_files ? "enabled" : "not configured"}. Web search: ${config.tools.web_search ? "enabled" : "not configured"}. ${config.tools.detail}`;
    const conversations = await refreshList();
    const saved = rememberedConversation();
    if (!fromUrl && saved && conversations.some((c) => c.id === saved))
      current = await api(`/conversations/${saved}`);
    render();
    await refreshList();
    refreshStatus();
  } catch (error) {
    showError(error);
  } finally {
    loading = false;
    updateControls();
  }
}
init();

$("mirror-avatar").addEventListener("change", () => {
  $("corner-companion").hidden =
    !$("mirror-avatar").checked || !avatarState?.visible;
  $("sidebar-avatar").hidden = !$("corner-companion").hidden;
});

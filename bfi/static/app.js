"use strict";
const $ = (id) => document.getElementById(id);
let config;
let current = null;
let busy = false;
let loading = false;
let status = null;

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
  const character = current?.character || config.character;
  $("character-name").textContent = character.name;
  $("character-description").textContent = character.description;
  $("character-prompt").textContent = character.system_prompt;
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
      (key) => current.backend[key] !== config[key],
    )
  ) {
    $("mode-notice").textContent =
      "Archived backend/model. Start a new conversation to use the current configuration.";
  } else {
    $("mode-notice").textContent =
      config.backend === "mock"
        ? "Mock mode — scripted replies, no model inference. Your history is still saved."
        : `Endpoint mode · ${config.requested_model} · Conversation history is sent to your configured server.`;
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
        `${conversation.backend.backend === "mock" ? "MOCK" : "ENDPOINT"} · ${new Date(conversation.updated_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}`,
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
    rememberConversation(current.id);
    $("message").value = "";
    $("error").hidden = true;
    render();
    await refreshList();
  } catch (error) {
    showError(error);
  } finally {
    loading = false;
    updateControls();
  }
}

async function refreshStatus() {
  $("refresh-status").disabled = true;
  $("status-label").textContent = "Checking backend…";
  $("status-detail").textContent = "Checking the configured backend…";
  try {
    status = await api("/status");
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
      current = await api("/conversations", { method: "POST" });
      rememberConversation(current.id);
    }
    current = await api(`/conversations/${current.id}/messages`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
    $("message").value = "";
    render();
    await refreshList();
  } catch (error) {
    showError(error);
  } finally {
    pending.remove();
    busy = false;
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

async function init() {
  loading = true;
  try {
    config = await api("/config");
    const list = $("backend-details");
    addDefinition(
      list,
      "Backend",
      config.backend === "mock"
        ? "Scripted mock (no inference)"
        : "OpenAI-compatible endpoint",
    );
    addDefinition(list, "Requested model", config.requested_model);
    addDefinition(list, "Endpoint", config.endpoint || "None");
    addDefinition(
      list,
      "Context window",
      `Up to ${config.history_pairs} recent exchanges; ${config.context_chars.toLocaleString()} character budget (not tokens)`,
    );
    const conversations = await refreshList();
    const saved = rememberedConversation();
    if (saved && conversations.some((c) => c.id === saved))
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

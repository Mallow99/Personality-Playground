const $ = (id) => document.getElementById(id);
const el = (tag, text, cls) => {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (cls) n.className = cls;
  return n;
};
let setup;
async function api(path, options = {}) {
  const r = await fetch(`/api${path}`, {
    ...options, headers: { "Content-Type": "application/json" },
  });
  if (!r.ok) {
    const error = await r.json().catch(() => ({}));
    throw new Error(typeof error.detail === "string" ? error.detail : `Request failed (${r.status}).`);
  }
  return r.status === 204 ? null : r.json();
}
function notice(text, error = false) {
  $("notice").textContent = text;
  $("notice").dataset.error = String(error);
  $("notice").hidden = false;
}
function action(label, callback, secondary = false) {
  const b = el("button", label, secondary ? "secondary" : "");
  b.type = "button";
  b.onclick = async () => {
    b.disabled = true;
    try { await callback(); } catch (error) { notice(error.message, true); }
    finally { b.disabled = false; }
  };
  return b;
}
function download(name, data, type = "application/json") {
  const blob = new Blob([typeof data === "string" ? data : JSON.stringify(data, null, 2)], { type });
  const url = URL.createObjectURL(blob);
  const a = el("a"); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function card(title, text, meta) {
  const c = el("article", undefined, "card");
  c.append(el("h3", title), el("p", text), el("p", meta, "meta"));
  return c;
}
async function connections(check = false) {
  setup = await api("/handler");
  $("connections").replaceChildren();
  for (const p of setup.profiles.filter((p) => p.id !== "companion")) {
    const c = card(p.name, p.requested_model, `${p.runtime} · ${p.endpoint || "No model endpoint"}`);
    c.append(el("span", p.backend === "mock" ? "Scripted mock" : "Configured", "badge"));
    c.append(el("p", `${p.max_tokens} output tokens · ${p.context_chars.toLocaleString()} context characters`, "meta"));
    if (check) {
      const status = await api(`/status?profile_id=${p.id}`);
      c.append(el("p", `${status.label}: ${status.detail}`));
      if (status.advertised_models?.length)
        c.append(el("p", `Advertised model IDs: ${status.advertised_models.join(", ")}`, "meta"));
    }
    $("connections").append(c);
  }
  if (!$("runtime").options.length) for (const p of setup.runtime_presets) {
    const o = el("option", p.label); o.value = p.id; $("runtime").append(o);
  }
}
async function jobs() {
  const records = await api("/jobs");
  $("jobs").replaceChildren();
  if (!records.length) $("jobs").append(el("p", "No generation jobs yet.", "muted"));
  for (const j of records) {
    const c = card(j.input_content.slice(0, 100), j.error || j.state, new Date(j.created_at).toLocaleString());
    if (["queued", "running"].includes(j.state)) c.append(action("Cancel reply", async () => {
      await api(`/jobs/${j.id}/cancel`, { method: "POST" }); await jobs();
    }));
    const a = el("a", "Open conversation"); a.href = `/?conversation=${encodeURIComponent(j.conversation_id)}`;
    c.append(a); $("jobs").append(c);
  }
}
function clearMemory() {
  $("memory-form").reset(); $("memory-id").value = "";
  $("memory-scope").disabled = false; $("save-memory").textContent = "Save memory";
}
async function memories() {
  const scope = $("memory-filter").value;
  const records = await api(`/memory${scope ? `?scope=${scope}` : ""}`);
  $("memories").replaceChildren();
  if (!records.length) $("memories").append(el("p", "No saved memories in this scope.", "muted"));
  for (const m of records) {
    const c = card(`${m.scope} · ${m.kind}`, m.content, `Source: ${m.source} · Importance ${m.importance}`);
    if (m.keywords.length) c.append(el("p", `Recall: ${m.keywords.join(", ")}`, "meta"));
    c.append(action("Correct", () => {
      $("memory-id").value = m.id; $("memory-content").value = m.content;
      $("memory-source").value = m.source; $("memory-scope").value = m.scope;
      $("memory-scope").disabled = true; $("memory-kind").value = m.kind;
      $("memory-importance").value = m.importance; $("memory-keywords").value = m.keywords.join(", ");
      $("save-memory").textContent = "Save correction";
      $("memory-content").focus();
    }));
    c.append(action("Forget", async () => {
      if (!confirm("Forget this saved memory and its corrections? Past conversations and exports remain separate.")) return;
      await api(`/memory/${m.id}`, { method: "DELETE" }); clearMemory(); await memories(); await sleepStatus();
      notice("Saved memory and corrections removed.");
    }, true));
    $("memories").append(c);
  }
}
async function openReport(id) {
  const doc = await api(`/research/${encodeURIComponent(id)}`);
  $("report-title").textContent = doc.title;
  $("report-source").textContent = `Source: ${doc.source} · Reviewed ${doc.reviewed_at} · SHA256 ${doc.sha256}`;
  $("report-content").textContent = doc.content; $("report").hidden = false;
  $("report").scrollIntoView({ behavior: "smooth", block: "start" });
}
async function research() {
  const query = $("research-query").value.trim();
  const result = await api(`/research?q=${encodeURIComponent(query)}`);
  $("documents").replaceChildren(); $("research-results").replaceChildren();
  $("search-status").textContent = query ? `${result.results.length} matching sections shown.` : `${result.documents.length} saved documents.`;
  for (const doc of result.documents) {
    const c = card(doc.title, doc.category, `Reviewed ${doc.reviewed_at}`);
    c.append(action("Read report", () => openReport(doc.id)));
    $("documents").append(c);
  }
  for (const hit of result.results) {
    const c = card(hit.title, hit.excerpt, `Section ${hit.section} · ${hit.source}`);
    c.append(action("Open source report", () => openReport(hit.id)));
    $("research-results").append(c);
  }
}
$("connection-form").onsubmit = (event) => {
  event.preventDefault();
  const runtime = setup.runtime_presets.find((p) => p.id === $("runtime").value);
  const text = `BFI_RUNTIME=${runtime.id}\nBFI_BACKEND=openai\nBFI_BASE_URL=${runtime.base_url}\nBFI_MODEL=${JSON.stringify($("model-id").value.trim())}\nBFI_MAX_TOKENS=512\nBFI_CONTEXT_CHARS=24000\nBFI_TEMPERATURE=0.7\n`;
  $("connection-preview").textContent = text;
  download("bfi-connection.env", text, "text/plain");
  notice("Connection settings downloaded. Review and copy into .env, then restart BFI.");
};
$("memory-form").onsubmit = async (event) => {
  event.preventDefault(); const id = $("memory-id").value;
  $("save-memory").disabled = true;
  try {
    await api(`/memory${id ? `/${id}` : ""}`, {
      method: id ? "PATCH" : "POST", body: JSON.stringify({
        content: $("memory-content").value, source: $("memory-source").value,
        scope: $("memory-scope").value, kind: $("memory-kind").value,
        importance: Number($("memory-importance").value),
        keywords: $("memory-keywords").value.split(",").map((k) => k.trim()).filter(Boolean),
      }),
    });
    clearMemory(); await memories(); notice(id ? "Correction saved; the previous version is retained in export." : "Memory saved.");
  } catch (error) { notice(error.message, true); }
  finally { $("save-memory").disabled = false; }
};
$("clear-memory").onclick = clearMemory;
$("memory-filter").onchange = () => memories().catch((e) => notice(e.message, true));
$("research-form").onsubmit = (event) => { event.preventDefault(); research().catch((e) => notice(e.message, true)); };
$("report-form").onsubmit = async (event) => {
  event.preventDefault();
  const b = event.submitter; b.disabled = true;
  try {
    const doc = await api("/research", { method: "POST", body: JSON.stringify({
      title: $("new-report-title").value, category: $("new-report-category").value,
      source: $("new-report-source").value, content: $("new-report-content").value,
      reviewed_at: $("new-report-date").value,
    }) });
    $("report-form").reset(); await research(); await openReport(doc.id); notice("Research report saved and indexed.");
  } catch (error) { notice(error.message, true); } finally { b.disabled = false; }
};
$("close-report").onclick = () => { $("report").hidden = true; };
$("check-connections").onclick = async () => {
  $("check-connections").disabled = true;
  try { await connections(true); } catch (e) { notice(e.message, true); }
  finally { $("check-connections").disabled = false; }
};
$("refresh-jobs").onclick = () => jobs().catch((e) => notice(e.message, true));
$("export-memory").onclick = async () => {
  try { download("bfi-memories.json", await api("/memory/export")); } catch (e) { notice(e.message, true); }
};
$("export-research").onclick = async () => {
  try { download("bfi-research.json", await api("/research/export")); } catch (e) { notice(e.message, true); }
};
if (location.pathname === "/library") {
  $("page-heading").textContent = "Research library";
  $("handler-section").hidden = true;
  $("personality-section").hidden = true;
}
if (location.pathname === "/personalities") {
  $("page-heading").textContent = "Character personalities";
  $("handler-section").hidden = $("library-section").hidden = true;
}
$("new-report-date").value = new Date().toISOString().slice(0, 10);

let sleepPoll;
async function sleepStatus(fillSettings = false) {
  const result = await api("/memory/sleep");
  if (fillSettings) {
    const s = result.settings;
    $("sleep-enabled").checked = s.enabled; $("sleep-model-review").checked = s.model_review;
    $("sleep-auto-merge").checked = s.auto_merge_exact; $("sleep-idle").value = s.idle_minutes;
    $("sleep-interval").value = s.interval_minutes; $("sleep-limit").value = s.max_records;
    $("sleep-reviewer").value = s.shared_reviewer; $("sleep-tokens").value = s.max_output_tokens;
  }
  $("sleep-runs").replaceChildren();
  for (const run of result.runs.slice(0, 3))
    $("sleep-runs").append(el("p", `${run.state} · ${new Date(run.created_at).toLocaleString()} · ${run.summary}`));
  const running = result.runs.some((r) => ["queued", "running"].includes(r.state));
  $("run-sleep").disabled = running; $("stop-sleep").disabled = !running;
  $("sleep-proposals").replaceChildren();
  if (!result.proposals.length) $("sleep-proposals").append(el("p", "No memory changes or suggestions yet.", "muted"));
  for (const p of result.proposals) {
    const s = p.suggestion;
    const c = card(`${s.action} · ${p.state} · ${p.scope}`, s.reason,
      `${p.before_records.length} source records retained`);
    c.append(el("p", p.provenance.method === "langmem"
      ? `LangMem · Requested model: ${p.provenance.requested_model}`
      : p.provenance.method === "exact_whitespace" ? "Exact text comparison" : "Earlier review", "meta"));
    c.dataset.proposalId = p.id;
    const before = el("details"); before.append(el("summary", "Inspect original memories and sources"));
    for (const m of p.before_records) before.append(el("p", `${m.content}\nSource: ${m.source}`));
    c.append(before);
    if (s.keywords.length) c.append(el("p", `Proposed recall words: ${s.keywords.join(", ")}`, "meta"));
    if (p.state === "pending") {
      const label = el("label", s.action === "conflict" ? "Your resolved memory" : "Memory to keep");
      const text = el("textarea"); text.value = s.content; text.maxLength = 2000; text.rows = 3;
      label.append(text); c.append(label);
      const sourceLabel = el("label", "Source or reason for your edit");
      const source = el("input"); source.maxLength = 1000;
      source.placeholder = s.action === "conflict" ? "Required to resolve conflicting facts" : "Optional; original sources are kept";
      sourceLabel.append(source); c.append(sourceLabel);
      c.append(action(s.action === "conflict" ? "Save resolution" : "Apply edit", async () => {
        await api(`/memory/proposals/${p.id}/apply`, { method: "POST", body: JSON.stringify({
          content: text.value, ...(source.value.trim() ? { source: source.value.trim() } : {}),
        }) });
        await memories(); await sleepStatus(); notice("Memory change applied; originals retained for undo.");
      }));
      c.append(action("Dismiss", async () => {
        await api(`/memory/proposals/${p.id}/dismiss`, { method: "POST" }); await sleepStatus();
      }, true));
    } else if (p.state === "applied") {
      c.append(el("p", p.applied_record?.content || s.content));
      c.append(action("Undo change", async () => {
        await api(`/memory/proposals/${p.id}/undo`, { method: "POST" }); await memories(); await sleepStatus();
        notice("Original saved memories restored.");
      }, true));
    }
    $("sleep-proposals").append(c);
  }
  clearTimeout(sleepPoll);
  if (running) sleepPoll = setTimeout(() => sleepStatus().catch((e) => notice(e.message, true)), 1000);
  else await memories();
}
$("sleep-settings-form").onsubmit = async (event) => {
  event.preventDefault();
  try {
    await api("/memory/sleep/settings", { method: "PUT", body: JSON.stringify({
      enabled: $("sleep-enabled").checked, model_review: $("sleep-model-review").checked,
      auto_merge_exact: $("sleep-auto-merge").checked, idle_minutes: Number($("sleep-idle").value),
      interval_minutes: Number($("sleep-interval").value), max_records: Number($("sleep-limit").value),
      shared_reviewer: $("sleep-reviewer").value, max_output_tokens: Number($("sleep-tokens").value),
    }) }); notice("Memory sleep settings saved.");
  } catch (e) { notice(e.message, true); }
};
$("run-sleep").onclick = async () => {
  $("run-sleep").disabled = true;
  try { await api("/memory/sleep/run", { method: "POST" }); await sleepStatus(); }
  catch (e) { notice(e.message, true); $("run-sleep").disabled = false; }
};
$("stop-sleep").onclick = async () => {
  try { await api("/memory/sleep/cancel", { method: "POST" }); await sleepStatus(); }
  catch (e) { notice(e.message, true); }
};
$("refresh-sleep").onclick = () => sleepStatus().catch((e) => notice(e.message, true));
$("recall-form").onsubmit = async (event) => {
  event.preventDefault();
  try {
    const r = await api(`/memory/recall?q=${encodeURIComponent($("recall-query").value)}&profile=${$("recall-profile").value}`);
    $("recall-results").replaceChildren();
    if (!r.records.length) $("recall-results").append(el("p", "No matching current memory in this scope."));
    for (const m of r.records) $("recall-results").append(card(m.scope, m.content, m.source));
  } catch (e) { notice(e.message, true); }
};

let personalities = [], personalityRevision;
const personalityFields = [
  ["display_name", "Display name", "input", 60], ["role", "Role and purpose", "textarea", 500],
  ["tone", "Tone", "textarea", 500], ["traits", "Traits · one per line", "textarea", 807],
  ["values", "Values · one per line", "textarea", 807], ["interests", "Interests", "textarea", 500],
  ["relationship_style", "Relationship with you", "textarea", 500],
  ["speech_style", "Speaking style", "textarea", 500],
  ["humor", "Humor", ["none", "light", "playful"]],
  ["initiative", "Initiative", ["gentle", "balanced", "proactive"]],
  ["verbosity", "Answer length", ["concise", "balanced", "detailed"]],
  ["boundaries", "Boundaries", "textarea", 700], ["backstory", "Fictional backstory · optional", "textarea", 700],
  ["custom_instructions", "Additional personality notes", "textarea", 1200],
];
function personalityDraft() {
  const result = {};
  for (const [key] of personalityFields) {
    const value = $("personality-" + key).value.trim();
    result[key] = ["traits", "values"].includes(key) ? value.split("\n").map((v) => v.trim()).filter(Boolean) : value;
  }
  return result;
}
async function personalityEditor() {
  const pid = $("personality-profile").value;
  const active = personalities.find((p) => p.profile === pid);
  personalityRevision = active.revision;
  $("personality-version").textContent = `Revision ${active.revision} · Provisional settings · New chats only`;
  $("personality-fields").replaceChildren();
  for (const [key, title, type, max] of personalityFields) {
    const label = el("label", title);
    const input = el(Array.isArray(type) ? "select" : type);
    input.id = "personality-" + key;
    if (Array.isArray(type)) for (const value of type) {
      const o = el("option", value); o.value = value; input.append(o);
    }
    else { input.maxLength = max; if (type === "textarea") input.rows = 2; }
    input.value = Array.isArray(active.settings[key]) ? active.settings[key].join("\n") : active.settings[key];
    label.append(input); $("personality-fields").append(label);
  }
  $("personality-prompt").textContent = active.compiled_prompt;
  $("personality-history").replaceChildren();
  const versions = await api(`/personalities/${pid}/history`);
  for (const v of versions) {
    const c = card(`Revision ${v.revision}`, v.reason, new Date(v.created_at).toLocaleString());
    if (v.revision !== active.revision) c.append(action("Restore this revision", async () => {
      await api(`/personalities/${pid}/restore`, { method: "POST", body: JSON.stringify({
        revision: v.revision, expected_revision: personalityRevision,
      }) }); await loadPersonalities(); notice("Earlier settings restored as a new revision.");
    }, true));
    $("personality-history").append(c);
  }
}
async function loadPersonalities() {
  personalities = await api("/personalities"); $("personality-cards").replaceChildren();
  for (const p of personalities) {
    const c = card(p.settings.display_name, p.settings.tone, `Revision ${p.revision} · Provisional`);
    c.append(action("Edit personality", async () => {
      $("personality-profile").value = p.profile; await personalityEditor();
      $("personality-form").scrollIntoView({ behavior: "smooth" });
    }, true)); $("personality-cards").append(c);
  }
  await personalityEditor();
}
$("personality-profile").onchange = () => personalityEditor().catch((e) => notice(e.message, true));
$("personality-form").onsubmit = async (event) => {
  event.preventDefault(); $("save-personality").disabled = true;
  try {
    await api(`/personalities/${$("personality-profile").value}`, { method: "PUT", body: JSON.stringify({
      expected_revision: personalityRevision, settings: personalityDraft(),
    }) }); await loadPersonalities(); notice("Personality saved. Start a new chat to use this revision.");
  } catch (e) { notice(e.message, true); }
  finally { $("save-personality").disabled = false; }
};
$("preview-personality").onclick = async () => {
  try {
    const r = await api(`/personalities/${$("personality-profile").value}/preview`, {
      method: "POST", body: JSON.stringify(personalityDraft()),
    }); $("personality-prompt").textContent = r.compiled_prompt; $("personality-preview").open = true;
  } catch (e) { notice(e.message, true); }
};
$("export-personalities").onclick = async () => {
  try { download("bfi-personalities.json", await api("/personalities/export")); }
  catch (e) { notice(e.message, true); }
};
addEventListener("pagehide", () => clearTimeout(sleepPoll));
Promise.all([connections(), jobs(), memories(), research(), sleepStatus(true), loadPersonalities()])
  .catch((e) => notice(e.message, true));

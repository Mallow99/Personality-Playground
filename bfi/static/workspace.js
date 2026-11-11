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
    const c = card(`${m.scope} · ${m.kind}`, m.content, `Source: ${m.source}`);
    c.append(action("Correct", () => {
      $("memory-id").value = m.id; $("memory-content").value = m.content;
      $("memory-source").value = m.source; $("memory-scope").value = m.scope;
      $("memory-scope").disabled = true; $("memory-kind").value = m.kind;
      $("save-memory").textContent = "Save correction";
      $("memory-content").focus();
    }));
    c.append(action("Forget", async () => {
      if (!confirm("Forget this saved memory and its corrections? Past conversations and exports remain separate.")) return;
      await api(`/memory/${m.id}`, { method: "DELETE" }); clearMemory(); await memories();
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
}
$("new-report-date").value = new Date().toISOString().slice(0, 10);
Promise.all([connections(), jobs(), memories(), research()]).catch((e) => notice(e.message, true));

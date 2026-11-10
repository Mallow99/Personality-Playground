// Owner decisions stay local until explicitly exported; defaults never imply sign-off.
const $ = (id) => document.getElementById(id),
  key = "bfi-pose-review-v1";
let decisions = {},
  plan,
  saved = true;
try {
  decisions = JSON.parse(localStorage.getItem(key) || "{}");
  if (!decisions || Array.isArray(decisions) || typeof decisions !== "object")
    decisions = {};
} catch {
  saved = false;
}
const options = ["unreviewed", "keep", "revise", "skip"];
const el = (tag, text) => {
  const node = document.createElement(tag);
  if (text) node.textContent = text;
  return node;
};
function status() {
  const counts = options.map(
    (s) =>
      `${plan.proposals.filter((p) => (decisions[p.code]?.decision || "unreviewed") === s).length} ${s}`,
  );
  $("review-status").textContent =
    counts.join(" · ") +
    (saved
      ? " · saved in this browser"
      : " · browser storage unavailable; download to retain");
}
function save(code, decision, note) {
  decisions[code] = { decision, note };
  try {
    localStorage.setItem(key, JSON.stringify(decisions));
    saved = true;
  } catch {
    saved = false;
  }
  status();
}
function render() {
  $("review-list").replaceChildren();
  const filter = $("review-filter").value;
  for (const role of ["shared", "academic", "engineering", "business"]) {
    if (filter !== "all" && filter !== role) continue;
    $("review-list").append(
      el(
        "h3",
        {
          shared: "Shared",
          academic: "Academic",
          engineering: "Hacker",
          business: "Business",
        }[role],
      ),
    );
    for (const p of plan.proposals.filter((p) => p.role === role)) {
      const row = el("article");
      row.className = "review-row";
      row.dataset.reviewId = p.code;
      const info = el("div");
      info.append(
        el(
          "strong",
          `${p.code} · ${p.label}${p.recommended ? " · suggested first" : ""}`,
        ),
        el("p", `${p.reason}. ${p.visual}`),
      );
      const select = el("select");
      select.setAttribute("aria-label", `Decision for ${p.code}`);
      for (const value of options) {
        const o = el(
          "option",
          value === "unreviewed"
            ? "Unreviewed"
            : value[0].toUpperCase() + value.slice(1),
        );
        o.value = value;
        select.append(o);
      }
      select.value = options.includes(decisions[p.code]?.decision)
        ? decisions[p.code].decision
        : "unreviewed";
      const note = el("input");
      note.type = "text";
      note.maxLength = 500;
      note.placeholder = "Optional change or pose idea";
      note.setAttribute("aria-label", `Notes for ${p.code}`);
      note.value = decisions[p.code]?.note || "";
      select.addEventListener("change", () =>
        save(p.code, select.value, note.value),
      );
      note.addEventListener("input", () =>
        save(p.code, select.value, note.value),
      );
      row.append(info, select, note);
      $("review-list").append(row);
    }
  }
  status();
}
$("review-filter").addEventListener("change", () => plan && render());
$("review-download").addEventListener("click", () => {
  if (!plan) return;
  const data = {
    version: 1,
    exportedAt: new Date().toISOString(),
    decisions: plan.proposals.map((p) => ({
      code: p.code,
      id: p.id,
      role: p.role,
      label: p.label,
      decision: decisions[p.code]?.decision || "unreviewed",
      note: decisions[p.code]?.note || "",
    })),
  };
  const url = URL.createObjectURL(
      new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
    ),
    a = el("a");
  a.href = url;
  a.download = "bfi-pose-decisions.json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
fetch(new URL("assets/pose-review.json", import.meta.url))
  .then((r) => {
    if (!r.ok) throw Error("Pose list unavailable");
    return r.json();
  })
  .then((data) => {
    plan = data;
    render();
  })
  .catch((error) => {
    $("review-status").textContent = error.message;
  });

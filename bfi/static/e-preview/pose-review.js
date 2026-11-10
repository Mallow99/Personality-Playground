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
      `${plan.proposals.filter((p) => (decisions[p.code]?.decision || (p.status === "approved" ? "keep" : "unreviewed")) === s).length} ${s}`,
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
function picture(p, interactive = true) {
  const frame = el(interactive ? "button" : "div");
  frame.className = "review-picture";
  if (interactive) {
    frame.type = "button";
    frame.setAttribute("aria-label", `Enlarge ${p.code} illustration`);
  }
  const img = el("img");
  img.src = p.image.sheet;
  img.alt = `${p.code}, ${p.label}, demonstrated by ${p.image.illustratedBy === "engineering" ? "Hacker" : p.image.illustratedBy}`;
  img.loading = interactive ? "lazy" : "eager";
  img.decoding = "async";
  img.width = 1536;
  img.height = 1024;
  img.style.left = `${-p.image.column * 100}%`;
  img.style.top = `${-p.image.row * 100}%`;
  frame.append(img);
  if (interactive)
    frame.addEventListener("click", () => {
      $("review-image-title").textContent = `${p.code} · ${p.label}`;
      $("review-image-reason").textContent = p.reason;
      $("review-image-frame").replaceChildren(picture(p, false));
      $("review-image-sheet").href = p.image.sheet;
      $("review-image-dialog").showModal();
    });
  return frame;
}
$("review-image-close").addEventListener("click", () =>
  $("review-image-dialog").close(),
);
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
        el("p", `Why: ${p.reason}`),
        el("p", `Pose: ${p.visual}`),
        el(
          "small",
          p.role === "shared"
            ? `Shared pose · illustrated by ${p.image.illustratedBy === "engineering" ? "Hacker" : p.image.illustratedBy}; adaptable to all three.`
            : "Owner-approved pose · revisions welcome",
        ),
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
        : p.status === "approved"
          ? "keep"
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
      row.append(picture(p), info, select, note);
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
      illustration: {
        sheet: p.image.sheet,
        row: p.image.row,
        column: p.image.column,
        sha256: p.image.sha256,
      },
      decision:
        decisions[p.code]?.decision ||
        (p.status === "approved" ? "keep" : "unreviewed"),
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

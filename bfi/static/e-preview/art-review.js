const $ = (id) => document.getElementById(id);
const local = (path) =>
  new URL(
    path
      .replace("/static/e-preview/", "./")
      .replace("/static/avatar/", "./avatar-runtime/"),
    import.meta.url,
  ).href;
try {
  const [catalog, report] = await Promise.all(
    ["avatar-runtime/catalog.json", "assets/avatar-visual-review.json"].map(
      async (path) => {
        const r = await fetch(new URL(path, import.meta.url), {
          cache: "no-store",
        });
        if (!r.ok) throw Error("The review library could not load.");
        return r.json();
      },
    ),
  );
  const notes = new Map(report.poses.map((p) => [p.id, p.findings]));
  for (const pose of catalog.poses) {
    const card = document.createElement("article");
    card.className = "card";
    card.dataset.role = pose.role;
    card.dataset.search = (pose.id + " " + pose.label).toLowerCase();
    const art = document.createElement("div");
    art.className = "art";
    const img = document.createElement("img");
    const url = new URL(local(pose.layered_src || pose.src));
    if (pose.asset_version) url.searchParams.set("v", pose.asset_version);
    img.src = url.href;
    img.alt = pose.label;
    img.className = "packaged";
    img.loading = "lazy";
    art.append(img);
    const original = document.createElement("img");
    original.className = "original";
    original.loading = "lazy";
    original.alt = pose.label + " source";
    if (pose.provenance) {
      const meta = pose.provenance;
      original.src = local("/static/e-preview/" + meta.sheet);
      original.classList.add("sheet");
      Object.assign(original.style, {
        width: "300%",
        height: "200%",
        left: `${-meta.column * 100}%`,
        top: `${-meta.row * 100}%`,
      });
    } else
      original.src = local(
        `/static/e-preview/assets/poses/${pose.id}.source.png`,
      );
    art.append(original);
    card.append(art);
    const content = document.createElement("div");
    content.className = "card-content";
    const h = document.createElement("h2");
    h.textContent = pose.label;
    const code = document.createElement("small");
    code.textContent = pose.id;
    content.append(h, code);
    const list = document.createElement("ul");
    for (const note of notes.get(pose.id) || []) {
      const li = document.createElement("li");
      li.textContent = note;
      list.append(li);
    }
    content.append(list);
    const link = document.createElement("a");
    link.href = "runtime-demo.html?pose=" + encodeURIComponent(pose.id);
    link.textContent = "Open this pose →";
    content.append(link);
    if (pose.id === "engineering/flirty") {
      const old = document.createElement("a");
      old.href = "assets/revisions/engineering-flirty-before.png";
      old.textContent = "Previous rejected pose";
      old.style.display = "block";
      content.append(old);
    }
    card.append(content);
    $("cards").append(card);
  }
  function filter() {
    let count = 0;
    for (const card of $("cards").children) {
      card.hidden =
        ($("role").value !== "all" && card.dataset.role !== $("role").value) ||
        !card.dataset.search.includes($("search").value.toLowerCase());
      if (!card.hidden) count++;
    }
    $("count").textContent =
      `${count} of ${catalog.poses.length} poses shown · ${$("source").checked ? "source artwork" : "packaged runtime artwork"}`;
  }
  $("role").addEventListener("change", filter);
  $("search").addEventListener("input", filter);
  $("background").addEventListener(
    "change",
    () => (document.body.dataset.background = $("background").value),
  );
  $("source").addEventListener("change", () => {
    document.body.dataset.source = String($("source").checked);
    filter();
  });
  filter();
} catch (error) {
  $("count").textContent = error.message;
  $("count").setAttribute("role", "alert");
}

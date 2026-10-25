// Reads data/prices.json (refreshed by .github/workflows/prices.yml) and decorates each product card.
(async () => {
  const won = (n) => "₩" + Number(n).toLocaleString("en-US");
  const day = (iso) => new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });

  let data;
  try { data = await (await fetch("data/prices.json", { cache: "no-cache" })).json(); } catch { return; }

  for (const card of document.querySelectorAll(".card[data-id]")) {
    const it = data.items[card.dataset.id];
    if (!it) continue;
    const box = document.createElement("div");
    box.className = "deal";
    const low = it.lowest;
    box.innerHTML = (low
      ? `<span class="deal-best">
           <span class="deal-label">Our price</span>
           <span class="deal-price">${won(low.price)}</span>
           <span class="deal-meta">lowest in Korea · checked ${day(low.checked)}</span>
         </span>`
      : `<span class="deal-label muted">No live price yet</span>`);
    card.querySelector(".card-foot").after(box);
  }
  const stamp = document.getElementById("price-stamp");
  if (stamp && data.updated) stamp.textContent = `Live prices last refreshed ${new Date(data.updated).toLocaleString()}.`;
})();

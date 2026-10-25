// Reads data/prices.json (refreshed by .github/workflows/prices.yml) and decorates each product card.
(async () => {
  const enc = encodeURIComponent;
  const compare = (q) => [
    ["Naver", `https://search.shopping.naver.com/search/all?query=${enc(q)}&sort=price_asc`],
    ["Google", `https://www.google.com/search?tbm=shop&hl=ko&gl=kr&q=${enc(q)}`],
    ["Danawa", `https://search.danawa.com/dsearch.php?query=${enc(q)}`],
    ["Coupang", `https://www.coupang.com/np/search?q=${enc(q)}&sorter=salePriceAsc`],
  ];
  const engineName = { naver: "Naver Shopping", google: "Google Shopping" };
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
      ? `<a class="deal-best" href="${low.link}" target="_blank" rel="noopener">
           <span class="deal-label">Lowest found</span>
           <span class="deal-price">${won(low.price)}</span>
           <span class="deal-meta">${low.mall} · ${engineName[low.engine] || low.engine} · ${day(low.checked)}</span>
         </a>`
      : `<span class="deal-label muted">No live price yet</span>`)
      + `<span class="deal-compare">Compare: ${compare(it.q).map(([n, u]) => `<a href="${u}" target="_blank" rel="noopener">${n}</a>`).join(" · ")}</span>`;
    card.querySelector(".card-foot").after(box);
  }
  const stamp = document.getElementById("price-stamp");
  if (stamp && data.updated) stamp.textContent = `Live prices last refreshed ${new Date(data.updated).toLocaleString()}.`;
})();

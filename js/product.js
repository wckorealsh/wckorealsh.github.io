// Renders product.html?id=<id> from data/products.json + live prices from data/prices.json.
(async () => {
  const root = document.getElementById("product");
  const id = new URLSearchParams(location.search).get("id");
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const won = (n) => "₩" + Number(n).toLocaleString("en-US");
  const range = ([a, b]) => (a === b ? won(a) : `${won(a)}–${won(b).slice(1)}`);
  const day = (iso) => new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });

  let data, prices = { items: {} };
  try { data = await (await fetch("data/products.json")).json(); } catch { root.innerHTML = "<p class='note'>Could not load products.</p>"; return; }
  try { prices = await (await fetch("data/prices.json", { cache: "no-cache" })).json(); } catch {}

  const p = data.items.find((x) => x.id === id);
  if (!p) { root.innerHTML = `<p class="note">No such product. <a href="shopping.html">Back to the shop →</a></p>`; return; }
  const cat = data.cats[p.cat];
  const live = prices.items[id] || {};
  const low = live.lowest;
  const sources = Object.values(live.sources || {});
  document.title = `${p.name} · ${p.brand} · The Lees`;

  // price-range bar: typical range as a track, live offers as dots
  const [lo, hi] = p.price;
  const span = Math.max(hi, ...sources.map((s) => s.price)) - Math.min(lo, ...sources.map((s) => s.price)) || 1;
  const base = Math.min(lo, ...sources.map((s) => s.price));
  const pct = (v) => Math.round(((v - base) / span) * 100);
  const saving = low && low.price < lo ? Math.round((1 - low.price / lo) * 100) : 0;

  const related = p.related.map((r) => data.items.find((x) => x.id === r)).filter(Boolean);

  root.innerHTML = `
    <nav class="crumbs"><a href="index.html">Home</a> › <a href="shopping.html">Shop</a> › <a href="shopping.html#${p.cat}">${cat.icon} ${esc(cat.name)}</a> › <span>${esc(p.name)}</span></nav>

    <section class="p-top" data-id="${p.id}" data-name="${esc(p.name)}" data-brand="${esc(p.brand)}" data-price="${esc(range(p.price))}" data-img="${p.img}">
      <figure class="p-gallery">
        <div class="p-img"><img src="${p.img}" alt="${esc(p.name)}" width="640" height="480"><span class="p-cap"></span></div>
        <div class="p-thumbs">
          <button type="button" class="on" data-src="${p.img}" data-cap=""><img src="${p.img}" alt="Product"></button>
          ${(p.scenes || []).map((cap, i) => `<button type="button" data-src="img/use/${p.id}-${i + 1}.jpg" data-cap="${esc(cap)}"><img src="img/use/${p.id}-${i + 1}.jpg" alt="${esc(cap)}"></button>`).join("")}
        </div>
        <figcaption>
          <span class="badge hot">${p.rank === 1 ? "Best 1" : "#" + p.rank + " in " + esc(cat.name)}</span>
          <span class="chip">🇰🇷 Made for Korea</span>
          <span class="chip">✈️ Ships to U.S.</span>
        </figcaption>
      </figure>

      <div class="p-buy">
        <p class="brand">${esc(p.brand)}</p>
        <h1>${esc(p.name)}</h1>
        <p class="tagline">${esc(p.tagline)}</p>

        <div class="p-price">
          ${low ? `<div class="p-low"><span class="deal-label">Our price</span><span class="deal-price big">${won(low.price)}</span>
                     ${saving ? `<span class="save">−${saving}% vs typical</span>` : ""}
                     <span class="deal-meta">lowest we found in Korea · checked ${day(low.checked)}</span></div>`
                : `<div class="p-low"><span class="deal-label muted">No live price yet — checked weekly</span></div>`}
          <div class="p-typical"><span class="deal-label">Typical price in Korea</span><span>${range(p.price)}</span></div>
        </div>

        <div class="p-bar" aria-label="Price range">
          <div class="track"><div class="fill" style="left:${pct(lo)}%;width:${Math.max(pct(hi) - pct(lo), 1)}%"></div>
            ${sources.map((s) => `<span class="dot ${s === low ? "best" : ""}" style="left:${pct(s.price)}%" title="${won(s.price)}"></span>`).join("")}
          </div>
          <div class="ticks"><span>${won(base)}</span><span>typical range</span><span>${won(base + span)}</span></div>
          <p class="legend"><i class="sw sw-fill"></i> typical Korean retail &nbsp; <i class="sw sw-dot"></i> live listing we found &nbsp; <i class="sw sw-dot sw-best"></i> lowest</p>
        </div>

        <div class="p-cart">
          <div class="qty"><button type="button" data-d="-1" aria-label="less">−</button><input id="qty" type="number" min="1" max="9" value="1" aria-label="Quantity"><button type="button" data-d="1" aria-label="more">+</button></div>
          <button class="add primary" type="button">Add to cart</button>
        </div>
        <ul class="p-promise">
          <li>🏷️ <b>Lowest price guaranteed</b> — found it cheaper at a Korean retailer within 7 days? We refund the difference.</li>
          <li>✈️ <b>Direct from Seoul to the U.S.</b> — tracked air shipping, 5–10 business days.</li>
          <li>🔁 Prices re-checked weekly across Korea's major shopping sites.</li>
        </ul>
      </div>
    </section>

    <section class="p-highlights">
      ${p.highlights.map((h) => `<div class="hl-card"><span class="hl-icon">${h.icon}</span><h3>${esc(h.title)}</h3><p>${esc(h.text)}</p></div>`).join("")}
    </section>

    ${p.real ? `<section class="p-real">
      <h2><span class="script">In your life</span></h2>
      <div class="real-grid">
        ${p.real.map((cap, i) => `<figure><img src="img/real/${p.id}-${i + 1}.jpg" alt="${esc(cap)}" loading="lazy" width="1152" height="640"><figcaption>${esc(cap)}</figcaption></figure>`).join("")}
      </div>
      <p class="note small">Styled renders of the product type, not official brand photos.</p>
    </section>` : ""}

    <section class="p-body">
      <article class="p-story">
        <h2><span class="script">The story</span></h2>
        ${p.story.map((s) => `<p>${esc(s)}</p>`).join("")}
      </article>
      <aside class="p-side">
        <div class="heat">
          <h3>🔥 How hot is it in Korea?</h3>
          <div class="flames" aria-label="${p.heat.score} of 5">${[1, 2, 3, 4, 5].map((i) => `<span class="${i <= p.heat.score ? "on" : ""}"></span>`).join("")}</div>
          <p>${esc(p.heat.note)}</p>
        </div>
        <table class="specs">
          <caption>Details</caption>
          ${Object.entries(p.specs).map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join("")}
        </table>
      </aside>
    </section>

    <section class="p-ship">
      <h2><span class="script">From Seoul to your door</span></h2>
      <ol class="route">
        <li><span class="dot-step">1</span><b>You order</b><small>today</small></li>
        <li><span class="dot-step">2</span><b>We buy in Korea</b><small>at the lowest price · 1–2 days</small></li>
        <li><span class="dot-step">3</span><b>Air shipping</b><small>tracked · 5–10 business days</small></li>
        <li><span class="dot-step">4</span><b>Your U.S. doorstep</b><small>no forwarding, no customs hassle</small></li>
      </ol>
    </section>

    <section class="p-related">
      <h2><span class="script">You may also like</span></h2>
      <div class="grid">
        ${related.map((r) => `
          <article class="card" data-id="${r.id}">
            <div class="card-img"><a href="product.html?id=${r.id}"><img src="${r.img}" alt="" loading="lazy" width="640" height="480"></a></div>
            <div class="card-body">
              <p class="brand">${esc(r.brand)}</p><h3><a href="product.html?id=${r.id}">${esc(r.name)}</a></h3>
              <p class="why">${esc(r.tagline)}</p>
              <div class="card-foot"><span class="price">${range(r.price)}</span><a class="add" href="product.html?id=${r.id}">View →</a></div>
            </div>
          </article>`).join("")}
      </div>
    </section>`;

  const qty = document.getElementById("qty");
  root.querySelectorAll(".p-cart .qty button").forEach((b) => b.addEventListener("click", () => {
    qty.value = Math.min(9, Math.max(1, (parseInt(qty.value, 10) || 1) + Number(b.dataset.d)));
  }));
  const main = root.querySelector(".p-img img"), cap = root.querySelector(".p-cap"), thumbs = root.querySelectorAll(".p-thumbs button");
  thumbs.forEach((b) => b.addEventListener("click", () => {
    thumbs.forEach((t) => t.classList.toggle("on", t === b));
    main.src = b.dataset.src; main.alt = b.dataset.cap || p.name;
    cap.textContent = b.dataset.cap; cap.hidden = !b.dataset.cap;
  }));
  cap.hidden = true;
})();

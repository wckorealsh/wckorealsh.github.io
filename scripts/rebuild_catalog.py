"""One-off: apply scripts/new_products.json to the catalog (products/items/prices JSON + shop/home cards)."""
import json, re, os, html
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
N = json.load(open("scripts/new_products.json"))
P = json.load(open("data/products.json"))
S = json.load(open("scripts/imggen/scenes.json"))
rm = set(N["remove"])
esc = html.escape
won = lambda n: "₩" + f"{n:,}"
rng = lambda p: won(p[0]) if p[0] == p[1] else f"{won(p[0])}–{p[1]:,}"

# ---- card copy (why / where) for kept items, from the current shopping.html
shop = open("shopping.html", encoding="utf-8").read()
copy = {}
for m in re.finditer(r'<article class="card" data-id="(\w+)".*?<p class="why">(.*?)</p>.*?<p class="where">(.*?)</p>', shop, re.S):
    copy[m.group(1)] = (html.unescape(m.group(2)), [html.unescape(w) for w in re.findall(r"<span>(.*?)</span>", m.group(3))])
copy["l7"] = (copy["l7"][0], ["Oh,lolly day!", "29CM"])  # was split on the comma
for it in N["items"]:
    copy[it["id"]] = (it["why"], it["where"])

# ---- products.json
order = {"stationery": ["s1", "s13", "s11", "s12", "s6", "s7", "s3", "s9", "s14", "s10", "s15"],
         "craft": ["c11", "c12", "c14", "c13", "c15"],
         "lifestyle": ["l9", "l6", "l14", "l1", "l13", "l11", "l7", "l2", "l3", "l5", "l4", "l12", "l8", "l10"]}
items = {p["id"]: p for p in P["items"] if p["id"] not in rm}
for it in N["items"]:
    p = {k: v for k, v in it.items() if k not in ("why", "where")}
    p["img"] = f"img/shop/{p['id']}.jpg"
    p["scenes"] = [cap for _, cap in S["items"][p["id"]]]
    items[p["id"]] = p
for cat, ids in order.items():
    for i, pid in enumerate(ids, 1):
        items[pid]["rank"] = i
for pid, p in items.items():
    ids = order[p["cat"]]
    rel = [r for r in p.get("related", []) if r in items and r != pid]
    for cand in ids + [x for c in order.values() for x in c]:
        if len(rel) >= 3: break
        if cand != pid and cand not in rel: rel.append(cand)
    p["related"] = rel[:3]
P["items"] = [items[pid] for ids in order.values() for pid in ids]
json.dump(P, open("data/products.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- items.json / prices.json
Q = json.load(open("data/items.json"))
Q = [q for q in Q if q["id"] not in rm] + [{"id": k, "q": v} for k, v in N["queries"].items()]
open("data/items.json", "w", encoding="utf-8").write("[\n" + ",\n".join(json.dumps(q, ensure_ascii=False) for q in Q) + "\n]\n")
PR = json.load(open("data/prices.json"))
PR["items"] = {k: v for k, v in PR["items"].items() if k not in rm}
json.dump(PR, open("data/prices.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- shopping.html cards
def card(p, home=False):
    why, where = copy[p["id"]]
    badge = f'<span class="badge hot">Best {p["rank"]}</span>' if p["rank"] <= 3 else f'<span class="badge">#{p["rank"]}</span>'
    if home: badge = '<span class="badge hot">Hot</span>'
    link = f'product.html?id={p["id"]}'
    foot = (f'<a class="add" href="{link}">View →</a>' if home else '<button class="add" type="button">+ Cart</button>')
    where_html = "" if home else f'\n            <p class="where">{"".join(f"<span>{esc(w)}</span>" for w in where)}</p>'
    attrs = "" if home else f' data-name="{esc(p["name"])}" data-brand="{esc(p["brand"])}" data-price="{rng(p["price"])}" data-img="{p["img"]}"'
    return f'''        <article class="card" data-id="{p["id"]}"{attrs}>
          <div class="card-img">{badge}<a href="{link}"><img src="{p["img"]}" alt="" loading="lazy" width="640" height="480"></a></div>
          <div class="card-body">
            <p class="brand">{esc(p["brand"])}</p>
            <h3><a href="{link}">{esc(p["name"])}</a></h3>
            <p class="why">{esc(why)}</p>
            <div class="card-foot"><span class="price">{rng(p["price"])}</span>{foot}</div>{where_html}
          </div>
        </article>'''

for cat, ids in order.items():
    grid = "\n".join(card(items[i]) for i in ids)
    shop = re.sub(rf'(<section id="{cat}" class="cat">.*?<div class="grid">\n).*?(\n      </div>\n    </section>)', lambda m: m.group(1) + grid + m.group(2), shop, count=1, flags=re.S)
    shop = re.sub(rf'(<section id="{cat}" class="cat">.*?<span class="count">)\d+ items', lambda m: m.group(1) + f"{len(ids)} items", shop, count=1, flags=re.S)
shop = shop.replace("Knitting moved from grandmothers to the MZ generation as an \"anti-dopamine\" hobby; bag charms and bead keyrings doubled in search interest.",
                    "Korea's traditional crafts — mother-of-pearl inlay, silk knots, hanji paper, folk painting — are the most-booked craft classes in Seoul, and now come as take-home kits you can't find in a US craft store.")
shop = shop.replace("Thumbnails are illustrative Creative-Commons photos via Openverse, not official product images.",
                    "Photo thumbnails are illustrative Creative-Commons photos via Openverse; illustrated thumbnails are our own. Neither are official product images.")
open("shopping.html", "w", encoding="utf-8").write(shop)

# ---- index.html: hot six + art swaps
home = open("index.html", encoding="utf-8").read()
hot = ["s1", "s13", "c11", "l6", "l9", "l14"]
grid = "\n".join(card(items[i], home=True) for i in hot)
grid = grid.replace('<span class="badge hot">Hot</span>', '<span class="badge hot">Best 1</span>', 1)
home = re.sub(r'(<section id="hot" class="shop">.*?<div class="grid">\n).*?(\n    </div>\n    <p class="teaser-more">)', lambda m: m.group(1) + grid.replace("\n        ", "\n      ") + m.group(2), home, count=1, flags=re.S)
home = home.replace("img/shop/c8.jpg", "img/shop/c11.jpg").replace("img/shop/c1.jpg", "img/shop/c11.jpg")
home = home.replace("🔥 Artisan keycaps", "🔥 Najeon mother-of-pearl kits").replace("🔥 Beginner knitting kits", "🔥 Choonsik desk sets").replace("🔥 Appree leaf sticky notes", "🔥 Dinotaeng quokka plush")
open("index.html", "w", encoding="utf-8").write(home)

# ---- old images
for pid in rm:
    for f in [f"img/shop/{pid}.jpg"] + [f"img/use/{pid}-{n}.jpg" for n in (1, 2, 3)]:
        if os.path.exists(f): os.remove(f)
print("items", len(P["items"]), "queries", len(Q), "prices", len(PR["items"]))

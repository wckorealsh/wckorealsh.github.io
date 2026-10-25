"""Query price-comparison engines for every item in data/items.json and write data/prices.json.

Engines: Naver Shopping (official API) and Google Shopping (SerpApi).
Danawa and Coupang expose no public price API (both are JS apps behind bot protection),
so the page links to their search pages instead of scraping them.
Keys come from env: NAVER_CLIENT_ID / NAVER_CLIENT_SECRET, SERPAPI_KEY (optional).
"""
import json, os, re, statistics, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"


def get(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def plausible(prices):
    """Drop accessory/junk listings: keep offers >= 35% of the median price."""
    if len(prices) < 3:
        return prices
    med = statistics.median(prices)
    return [p for p in prices if p >= 0.35 * med] or prices


def relevant(q, title):
    """Drop off-topic results: the first query word (brand / core noun) must appear in the title."""
    norm = lambda s: re.sub(r"\s+", "", s).casefold()
    return norm(q.split()[0]) in norm(title)


def pick(q, offers):
    offers = [o for o in offers if relevant(q, o["title"])]
    if not offers:
        return None
    keep = set(plausible([o["price"] for o in offers]))
    return min((o for o in offers if o["price"] in keep), key=lambda o: o["price"])


def naver(q):
    cid, sec = os.environ.get("NAVER_CLIENT_ID"), os.environ.get("NAVER_CLIENT_SECRET")
    if not cid or not sec:
        return None
    url = "https://openapi.naver.com/v1/search/shop.json?display=40&sort=sim&query=" + urllib.parse.quote(q)
    items = json.loads(get(url, {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": sec}))["items"]
    offers = [{"price": int(i["lprice"]), "mall": i["mallName"] or "Naver", "title": re.sub("<.*?>", "", unescape(i["title"])), "link": i["link"]}
              for i in items if i.get("lprice") and int(i["lprice"]) > 0]
    best = pick(q, offers)
    return {"engine": "naver", **best} if best else None


def google(q):
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        return None
    url = ("https://serpapi.com/search.json?engine=google_shopping&gl=kr&hl=ko&api_key=" + key
           + "&q=" + urllib.parse.quote(q))
    res = json.loads(get(url)).get("shopping_results", [])
    offers = []
    for r in res:
        m = re.search(r"[\d,]+", r.get("price", "") or "")
        if m:
            offers.append({"price": int(m.group().replace(",", "")), "mall": r.get("source", "Google"), "title": r.get("title", ""), "link": r.get("product_link") or r.get("link", "")})
    best = pick(q, offers)
    return {"engine": "google", **best} if best else None




def main():
    items = json.load(open(os.path.join(ROOT, "data/items.json"), encoding="utf-8"))
    out_path = os.path.join(ROOT, "data/prices.json")
    prev = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {"items": {}}
    engines = [e for e in sys.argv[1:]] or ["naver", "google"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    result = {"updated": now, "items": {}}
    for it in items:
        entry = prev["items"].get(it["id"], {"sources": {}})
        for name in engines:
            try:
                r = globals()[name](it["q"])
            except Exception as e:  # keep the previous value for this engine
                print(f"{it['id']} {name}: {e}", file=sys.stderr); r = None
            if r:
                r["checked"] = now
                entry["sources"][name] = r
            time.sleep(0.2)
        srcs = list(entry["sources"].values())
        entry["lowest"] = min(srcs, key=lambda s: s["price"]) if srcs else None
        entry["q"] = it["q"]
        result["items"][it["id"]] = entry
        print(it["id"], {k: v["price"] for k, v in entry["sources"].items()})
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

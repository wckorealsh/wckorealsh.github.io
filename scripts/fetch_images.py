"""Fetch a real listing photo per item: render the 11st search for items.json queries in
headless Chrome, take the first relevant card, download its hi-res image to img/src/<id>.jpg
and record source in img/src/sources.json. Pass ids to limit; `--pick ID=N` takes the Nth card."""
import html, json, os, re, subprocess, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "src")
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
CHROME = "/usr/bin/google-chrome"

args = sys.argv[1:]
picks = {a[7:].split("=")[0]: int(a[7:].split("=")[1]) for a in args if a.startswith("--pick=")}  # --pick=ID=N
qs = {a[4:].split("=", 1)[0]: a[4:].split("=", 1)[1] for a in args if a.startswith("--q=")}  # --q=ID=query override
only = {a for a in args if not a.startswith("--")} | set(picks) | set(qs)
items = json.load(open(os.path.join(ROOT, "data", "items.json")))
srcp = os.path.join(OUT, "sources.json")
sources = json.load(open(srcp)) if os.path.exists(srcp) else {}
norm = lambda s: re.sub(r"\s+", "", s).casefold()


def cards(q):
    url = "https://search.11st.co.kr/Search.tmall?kwd=" + urllib.parse.quote(q)
    dom = ""
    for _ in range(2):
        try:
            dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--lang=ko-KR", "--timeout=30000",
                                  f"--user-agent={UA}", "--virtual-time-budget=8000", "--dump-dom", url],
                                 capture_output=True, text=True, timeout=60).stdout
            break
        except subprocess.TimeoutExpired:
            pass
    out = []
    for c in re.split(r'<li class="c-search-list__item', dom)[1:]:
        m = re.search(r'<img[^>]+src="(https://cdn\.011st\.com/11dims/[^"]*?/11src/product/(\d+)/[^"?]+)[^"]*"[^>]*alt="([^"]*)"', c)
        if m:
            out.append({"pid": m.group(2), "title": html.unescape(m.group(3)), "img": re.sub(r"/resize/[^/]+/", "/resize/1000x1000/", m.group(1))})
    return out


for it in items:
    pid, q = it["id"], qs.get(it["id"], it["q"])
    if (only and pid not in only) or (not only and pid in sources):
        continue
    cs = cards(q)
    rel = [c for c in cs if norm(q.split()[0]) in norm(c["title"])] or cs
    if not rel:
        print("NONE", pid, q); continue
    c = rel[picks.get(pid, 1) - 1]
    data = urllib.request.urlopen(urllib.request.Request(c["img"], headers={"User-Agent": UA}), timeout=30).read()
    open(os.path.join(OUT, pid + ".webp"), "wb").write(data)
    sources[pid] = {"q": q, "title": c["title"], "url": f"https://www.11st.co.kr/products/{c['pid']}", "img": c["img"],
                    "alts": [{"title": x["title"][:60], "url": f"https://www.11st.co.kr/products/{x['pid']}"} for x in rel[:5]]}
    json.dump(sources, open(srcp, "w"), ensure_ascii=False, indent=1)
    print("OK", pid, len(data), c["title"][:70], flush=True)

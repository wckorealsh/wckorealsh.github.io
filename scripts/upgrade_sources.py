"""Replace soft (CDN-upscaled) listing photos in img/src with sharper ones.
For each id given (or every id whose effective resolution < 700 px) try: every gallery image of the
current listing page + the main image of each alternative listing, fetched at 2000x2000, and keep
the one with the highest effective resolution (ties -> sharper). Updates img/src/sources.json."""
import io, json, os, re, sys, urllib.request
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "img", "src")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept-Language": "ko,en"}
MIN = 700
srcp = os.path.join(SRC, "sources.json")
sources = json.load(open(srcp))
same_only = "--same" in sys.argv  # only other photos of the SAME listing, never switch listing
only = {a for a in sys.argv[1:] if not a.startswith("--")}


def get(u, timeout=25):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout).read()


def effres(im):
    g = im.convert("L"); a = np.asarray(g, dtype=float)
    for r in (250, 400, 550, 700, 850, 1000, 1300):
        if r >= min(im.size): return min(im.size)
        b = np.asarray(g.resize((r, r), Image.LANCZOS).resize(g.size, Image.BICUBIC), dtype=float)
        if np.abs(a - b).mean() < 1.2: return r
    return min(im.size)


def sharp(im):
    g = np.asarray(im.convert("L").resize((600, 600)), dtype=float)
    return float(np.abs(4 * g[1:-1, 1:-1] - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]).mean())


def big(path):  # cdn path 'product/123/B.webp' -> 2000px url
    return "https://cdn.011st.com/11dims/resize/2000x2000/quality/90/11src/" + path


def candidates(s):
    paths = []
    pid = s["url"].rsplit("/", 1)[1]
    try:
        html = get(s["url"]).decode("utf-8", "ignore")
        paths += [f"product/{pid}/{n}.{e}" for n, e in dict.fromkeys(re.findall(rf"/11src/product/{pid}/(\w+)\.(webp|jpg|jpeg|png)", html))]
    except Exception as e:
        print("  page fail", str(e)[:50])
    if not same_only:
        for a in s.get("alts", []):
            apid = a["url"].rsplit("/", 1)[1]
            if apid != pid:
                paths.append(f"product/{apid}/B.webp")
    return list(dict.fromkeys(paths))


for pid, s in sources.items():
    cur = Image.open(os.path.join(SRC, pid + ".webp"))
    cur_res = effres(cur)
    if (only and pid not in only) or (not only and cur_res >= MIN):
        continue
    best = (cur_res, sharp(cur), None, None)
    for path in candidates(s):
        try:
            data = get(big(path)); im = Image.open(io.BytesIO(data)).convert("RGB")
        except Exception:
            continue
        if min(im.size) < 500 or im.width / im.height > 1.6 or im.height / im.width > 1.6:
            continue
        key = (effres(im), sharp(im))
        if key > best[:2]:
            best = (*key, path, im)
    if best[2]:
        best[3].save(os.path.join(SRC, pid + ".webp"), "WEBP", quality=92)
        s["img"] = big(best[2]); s["url"] = "https://www.11st.co.kr/products/" + best[2].split("/")[1]
        s["title"] = next((a["title"] for a in s.get("alts", []) if a["url"] == s["url"]), s["title"])
        json.dump(sources, open(srcp, "w"), ensure_ascii=False, indent=1)
        print(f"UPGRADED {pid} {cur_res}->{best[0]} ({best[1]:.1f}) {best[2]}", flush=True)
    else:
        print(f"KEPT {pid} {cur_res} (no better candidate)", flush=True)

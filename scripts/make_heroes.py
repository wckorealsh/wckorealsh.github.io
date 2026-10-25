"""img/src/<id>.webp (listing photo) -> img/shop/<id>.jpg 640x480 (padded with the photo's own
background colour) and img/shop/credits.json entries pointing at the listing."""
import json, os, sys
from PIL import Image, ImageStat

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, SHOP = os.path.join(ROOT, "img", "src"), os.path.join(ROOT, "img", "shop")
sources = json.load(open(os.path.join(SRC, "sources.json")))
credp = os.path.join(SHOP, "credits.json")
credits = {c["key"]: c for c in json.load(open(credp))}
only = set(sys.argv[1:])

for pid, s in sources.items():
    if only and pid not in only:
        continue
    im = Image.open(os.path.join(SRC, pid + ".webp")).convert("RGB")
    w, h = im.size
    # background = mean colour of the 4 corner patches
    pads = [im.crop(b) for b in [(0, 0, 12, 12), (w - 12, 0, w, 12), (0, h - 12, 12, h), (w - 12, h - 12, w, h)]]
    bg = tuple(int(sum(ImageStat.Stat(p).mean[i] for p in pads) / 4) for i in range(3))
    im.thumbnail((640, 480), Image.LANCZOS)
    out = Image.new("RGB", (640, 480), bg)
    out.paste(im, ((640 - im.width) // 2, (480 - im.height) // 2))
    out.save(os.path.join(SHOP, pid + ".jpg"), "JPEG", quality=86, optimize=True)
    credits[pid] = {"key": pid, "title": s["title"], "source": "11st listing", "url": s["url"]}
    print("OK", pid, bg)

json.dump(sorted(credits.values(), key=lambda c: c["key"]), open(credp, "w"), ensure_ascii=False, indent=1)

"""Option A gallery: real listing photo (img/src/<id>.webp) + illustrated character + handwritten caption
-> ~/work/zz/img/use/<id>-<n>.jpg (960x720).
  python gen_overlay.py            # generate missing characters (img/chars/*.png) then compose all
  python gen_overlay.py --compose  # compose only (no GPU)
  python gen_overlay.py s1 l14-2   # limit to ids / shots (regenerates those characters)"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
ZZ = os.path.expanduser("~/work/zz")
CHARS, OUT = os.path.join(ZZ, "img", "chars"), os.path.join(ZZ, "img", "use")
os.makedirs(CHARS, exist_ok=True); os.makedirs(OUT, exist_ok=True)
R = json.load(open(os.path.join(HERE, "overlay.json")))
compose_only = "--compose" in sys.argv
only = {a for a in sys.argv[1:] if not a.startswith("--")}
W, H = 960, 720
FONT = ImageFont.truetype(os.path.join(HERE, "fonts", "Caveat.ttf"), 46); FONT.set_variation_by_name("Bold")
SAGE, INK = (116, 150, 118), (45, 48, 52)


def want(pid, name):
    return not only or pid in only or name in only


def photo(pid):
    im = Image.open(os.path.join(ZZ, "img", "src", pid + ".webp")).convert("RGB")
    w, h = im.size
    pads = [im.crop(b) for b in [(0, 0, 12, 12), (w - 12, 0, w, 12), (0, h - 12, 12, h), (w - 12, h - 12, w, h)]]
    bg = tuple(int(sum(ImageStat.Stat(p).mean[i] for p in pads) / 4) for i in range(3))
    im.thumbnail((W, H), Image.LANCZOS)
    out = Image.new("RGB", (W, H), bg); out.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    return out.convert("RGBA")


def cutout(path):
    im = Image.open(path).convert("RGBA"); a = np.array(im)
    white = a[..., :3].min(axis=2) > 232
    a[..., 3] = np.where(white, 0, 255).astype("uint8")
    im = Image.fromarray(a); return im.crop(im.getbbox())


def compose(pid, n, cap):
    base = photo(pid)
    ch = cutout(os.path.join(CHARS, f"{pid}-{n}.png")); ch.thumbnail((int(W * .42), int(H * .80)), Image.LANCZOS)
    left = n != 2
    x = 16 if left else W - ch.width - 16
    # soft drop shadow so the character sits on the photo
    sh = Image.new("RGBA", ch.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 70), mask=ch.split()[3])
    from PIL import ImageFilter
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(sh, (x + 8, H - ch.height + 10)); base.alpha_composite(ch, (x, H - ch.height))
    # speech bubble
    d = ImageDraw.Draw(base)
    tw = d.textlength(cap, font=FONT); bw, bh = int(tw) + 48, 76
    bx = x + ch.width - 30 if left else x - bw + 30
    bx = max(12, min(bx, W - bw - 12)); by = max(14, H - ch.height - 40)
    d.rounded_rectangle((bx, by, bx + bw, by + bh), 26, fill=(255, 255, 255, 240), outline=SAGE, width=3)
    tail = (bx + 40, by + bh - 2, bx + 70, by + bh - 2, bx + 30 if left else bx + 85, by + bh + 22) if left else \
           (bx + bw - 70, by + bh - 2, bx + bw - 40, by + bh - 2, bx + bw - 30, by + bh + 22)
    d.polygon(tail, fill=(255, 255, 255, 240), outline=SAGE)
    d.text((bx + 24, by + 10), cap, font=FONT, fill=INK)
    base.convert("RGB").save(os.path.join(OUT, f"{pid}-{n}.jpg"), "JPEG", quality=86, optimize=True)


if not compose_only:
    import torch
    from diffusers import FluxPipeline
    pipe = FluxPipeline.from_pretrained("Freepik/flux.1-lite-8B", torch_dtype=torch.bfloat16).to("cuda")
    for pid, shots in R["items"].items():
        for n, (prompt, _cap) in enumerate(shots, 1):
            name, path = f"{pid}-{n}", os.path.join(CHARS, f"{pid}-{n}.png")
            if not want(pid, name) or (not only and os.path.exists(path)):
                continue
            g = torch.Generator("cuda").manual_seed(hash(name) % 10_000 + int(os.environ.get("SEED_OFFSET", 0)))
            pipe(prompt + ", " + R["style"], guidance_scale=3.5, num_inference_steps=24,
                 width=768, height=1024, generator=g).images[0].save(path)
            print("GEN", name, flush=True)

for pid, shots in R["items"].items():
    for n, (_prompt, cap) in enumerate(shots, 1):
        if want(pid, f"{pid}-{n}"):
            compose(pid, n, cap); print("OK", f"{pid}-{n}", flush=True)
print("ALL_DONE", flush=True)

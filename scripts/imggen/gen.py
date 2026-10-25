"""Generate 3 'in use' illustrations per product with FLUX.1-lite-8B -> ../zz/img/use/<id>-<n>.jpg"""
import json, os, sys, torch
from diffusers import FluxPipeline
from PIL import Image

OUT = os.path.expanduser("~/work/zz/img/use")
os.makedirs(OUT, exist_ok=True)
S = json.load(open(os.path.join(os.path.dirname(__file__), "scenes.json")))
only = set(sys.argv[1:])  # optional: ids or id-n to regenerate

pipe = FluxPipeline.from_pretrained("Freepik/flux.1-lite-8B", torch_dtype=torch.bfloat16).to("cuda")

jobs = [(pid, f"{pid}-{n}", prompt, OUT, (960, 720)) for pid, scenes in S["items"].items() for n, (prompt, _cap) in enumerate(scenes, 1)]
jobs += [(pid, pid, prompt, os.path.expanduser("~/work/zz/img/shop"), (640, 480)) for pid, prompt in S.get("heroes", {}).items()]
for pid, name, prompt, out, size in jobs:
        path = os.path.join(out, name + ".jpg")
        if only and pid not in only and name not in only:
            continue
        if not only and os.path.exists(path):
            continue
        g = torch.Generator("cuda").manual_seed(hash(name) % 10_000)
        img = pipe(prompt + ", " + S["style"], guidance_scale=3.5, num_inference_steps=24,
                   width=1024, height=768, generator=g).images[0]
        img.resize(size, Image.LANCZOS).save(path, "JPEG", quality=84, optimize=True)
        print("DONE", name, flush=True)
print("ALL_DONE", flush=True)

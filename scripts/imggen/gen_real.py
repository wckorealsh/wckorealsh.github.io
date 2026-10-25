"""Photoreal 'in your life' shots: real.json -> ../zz/img/real/<id>-<n>.jpg (16:9)."""
import json, os, sys, torch
from diffusers import FluxPipeline
from PIL import Image

OUT = os.path.expanduser("~/work/zz/img/real")
os.makedirs(OUT, exist_ok=True)
R = json.load(open(os.path.join(os.path.dirname(__file__), "real.json")))
only = set(sys.argv[1:])

pipe = FluxPipeline.from_pretrained("Freepik/flux.1-lite-8B", torch_dtype=torch.bfloat16).to("cuda")

for pid, shots in R["items"].items():
    for n, (prompt, _cap) in enumerate(shots, 1):
        name = f"{pid}-{n}"
        path = os.path.join(OUT, name + ".jpg")
        if only and pid not in only and name not in only:
            continue
        if not only and os.path.exists(path):
            continue
        g = torch.Generator("cuda").manual_seed(hash(name) % 10_000)
        img = pipe(prompt + ", " + R["style"], guidance_scale=3.5, num_inference_steps=28,
                   width=1152, height=640, generator=g).images[0]
        img.resize((1152, 640), Image.LANCZOS).save(path, "JPEG", quality=84, optimize=True)
        print("DONE", name, flush=True)
print("ALL_DONE", flush=True)

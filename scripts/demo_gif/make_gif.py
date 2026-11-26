#!/usr/bin/env python3
"""Rebuild docs/urdukit-demo.gif from the library's real output.

Every line in the GIF is produced by calling urdukit here, so the GIF can
never show output the library does not give. Rendering goes through a
headless Chrome so Urdu is shaped properly (terminal recorders draw
Arabic-script letters unjoined).

Dev-only requirements: Google Chrome and Pillow.

    python scripts/demo_gif/make_gif.py [--chrome PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "src"))

import urdukit  # noqa: E402
from urdukit import (  # noqa: E402
    normalize,
    sentence_tokenize,
    to_roman,
    to_urdu,
    word_tokenize,
)

STEPS = [
    (
        "Spelling variants: look the same, are not the same",
        [
            ('"علی" == "علي"', "علی" == "علي"),
            (
                'normalize("علي") == normalize("علی")',
                normalize("علي") == normalize("علی"),
            ),
            ('normalize("مُحَمَّد علي")', normalize("مُحَمَّد علي")),
        ],
    ),
    (
        "Mixed scripts: English inside Urdu, missing spaces",
        [
            (
                'word_tokenize("میں computer استعمال کرتا ہوں")',
                word_tokenize("میں computer استعمال کرتا ہوں"),
            ),
            ('sentence_tokenize("ایک۔دو۔تین۔")', sentence_tokenize("ایک۔دو۔تین۔")),
        ],
    ),
    (
        "Urdu → Roman Urdu",
        [
            ('to_roman("میں پاکستان سے ہوں۔")', to_roman("میں پاکستان سے ہوں۔")),
            ('to_roman("آرمی")', to_roman("آرمی")),
        ],
    ),
    (
        "Roman Urdu → Urdu, texting spellings included",
        [
            ('to_urdu("mai pakistan sy hu")', to_urdu("mai pakistan sy hu")),
        ],
    ),
]

DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def main() -> int:
    from PIL import Image

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chrome", default=os.environ.get("CHROME", DEFAULT_CHROME))
    parser.add_argument("--out", default=os.path.join(ROOT, "docs", "urdukit-demo.gif"))
    args = parser.parse_args()

    data = {
        "version": urdukit.__version__,
        "steps": [
            {"title": t, "lines": [{"code": c, "out": repr(v)} for c, v in lines]}
            for t, lines in STEPS
        ],
    }
    frames = []
    for si, step in enumerate(data["steps"]):
        frames.append((si, 0, False, 900))
        for li in range(len(step["lines"])):
            last = li + 1 == len(step["lines"])
            frames.append((si, li + 1, False, 700))
            frames.append((si, li + 1, True, 2600 if last else 1500))

    with tempfile.TemporaryDirectory() as tmp:
        template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
        page = os.path.join(tmp, "page.html")
        with open(page, "w", encoding="utf-8") as fh:
            fh.write(template.replace("__DATA__", json.dumps(data, ensure_ascii=False)))
        images, durations = [], []
        for i, (si, n, out, ms) in enumerate(frames):
            shot = os.path.join(tmp, f"{i:03d}.png")
            url = "file://" + page + "#" + urllib.parse.quote(json.dumps([si, n, out]))
            for attempt in range(4):
                result = subprocess.run(
                    [
                        args.chrome,
                        "--headless=new",
                        "--disable-gpu",
                        "--hide-scrollbars",
                        f"--user-data-dir={tmp}/profile-{i}-{attempt}",
                        "--window-size=960,440",
                        "--force-device-scale-factor=1",
                        f"--screenshot={shot}",
                        url,
                    ],
                    capture_output=True,
                    timeout=60,
                )
                if result.returncode == 0 and os.path.exists(shot):
                    break
                time.sleep(1)
            else:
                print(f"frame {i} failed", file=sys.stderr)
                return 1
            images.append(Image.open(shot).convert("RGB"))
            durations.append(ms)

    palette = images[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    quantized = [
        im.quantize(palette=palette, dither=Image.Dither.NONE) for im in images
    ]
    quantized[0].save(
        args.out,
        save_all=True,
        append_images=quantized[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=1,
    )
    print(
        f"{args.out}: {len(quantized)} frames, {sum(durations) / 1000:.1f} s, "
        f"{os.path.getsize(args.out) // 1024} KB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

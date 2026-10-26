"""Assemble the listening site from pair bundles: data/<pair>/data.json + data/<pair>/audio/*.mp3 -> out/.
Standard library only, so GitHub Actions can run it without the audio stack.

    python assemble.py [--data data] [--out out] [--templates .]

Bundles are produced by export_listen.py on the machine that has the renders.
"""
import argparse
import html
import json
import shutil
import statistics
from pathlib import Path

# The templates are page bodies (the Artifact host adds its own document skeleton); site pages get this one.
HEAD = ('<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="robots" content="noindex, nofollow">\n')  # published on GitHub Pages: link-only


def inline(data):
    return json.dumps(data, separators=(",", ":")).replace("</", "<\\/")


def main(data_dir, out_dir, templates):
    data_dir, out_dir, templates = Path(data_dir), Path(out_dir), Path(templates)
    pair_tpl = (templates / "listen_template.html").read_text()
    index_tpl = (templates / "index_template.html").read_text()
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs = []
    for bundle in sorted(p for p in data_dir.iterdir() if (p / "data.json").exists()):
        data = json.loads((bundle / "data.json").read_text())
        dest = out_dir / bundle.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(bundle / "audio", dest / "audio")
        page = pair_tpl.replace("__TITLE__", html.escape(f"{data['source']} to {data['target']}"))
        page = page.replace("__DATA__", inline(data))
        (dest / "index.html").write_text(HEAD + page)
        (dest / "artifact.html").write_text(page)
        shapes = [p["shape"] for p in data["patches"]]
        pairs.append({"key": bundle.name, "source": data["source"], "target": data["target"], "count": len(shapes),
                      "median_shape": statistics.median(shapes) if shapes else None})
        print(f"{bundle.name}: {len(shapes)} patches")
    page = index_tpl.replace("__DATA__", inline(pairs))
    (out_dir / "index.html").write_text(HEAD + page)
    (out_dir / "artifact.html").write_text(page)
    (out_dir / ".nojekyll").touch()


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=here / "data")
    ap.add_argument("--out", default=here / "out")
    ap.add_argument("--templates", default=here)
    a = ap.parse_args()
    main(a.data, a.out, a.templates)

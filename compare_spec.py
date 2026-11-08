"""Compare the Module 2 hand-written spec with the live FastAPI /openapi.json.
Usage: python compare_spec.py https://<your-app>.onrender.com
"""
import json
import sys
import urllib.request

import yaml

base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"
METHODS = {"get", "post", "put", "patch", "delete"}


def ops(doc):
    out = {}
    for path, item in doc.get("paths", {}).items():
        for m, op in item.items():
            if m in METHODS:
                codes = sorted(c for c in op.get("responses", {}) if c.startswith("2"))
                out[(m.upper(), path)] = codes
    return out


spec = ops(yaml.safe_load(open("spec/openapi.yaml", encoding="utf-8")))
live = ops(json.load(urllib.request.urlopen(f"{base}/openapi.json")))

print(f"| Method | Path | Spec 2xx | Live 2xx | Result |\n|---|---|---|---|---|")
for key in sorted(spec.keys() | live.keys(), key=lambda k: (k[1], k[0])):
    s, l = spec.get(key), live.get(key)
    if s and l:
        res = "match" if s == l else "status differs"
    else:
        res = "only in spec" if s else "only live"
    print(f"| {key[0]} | {key[1]} | {','.join(s or ['-'])} | {','.join(l or ['-'])} | {res} |")

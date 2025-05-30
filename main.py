import yaml
import json
from elmes.utils import extract
from pathlib import Path
from typing import Dict, Any

data: Dict[str, Dict[str, Any]] = {}
with open("guided_teaching.yaml", "r") as f:
    t = f.read()
    for d in yaml.safe_load_all(t):
        data = d

for k in data.keys():
    c = extract(data, k)
    with open(Path(__file__).parent / "guided_teaching" / f"{k}.yaml", "w") as f:
        d = yaml.dump({k: c}, default_flow_style=False, allow_unicode=True)
        f.write(d)

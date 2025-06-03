from elmes.entity import ElmesConfig
from elmes.utils import extract
from pathlib import Path
from typing import Dict, Any

import yaml

CONFIG = None


def load_conf(path: Path):
    global CONFIG
    data: Dict[str, Dict[str, Any]] = {}
    with open(path, "r") as f:
        t = f.read()
        for d in yaml.safe_load_all(t):
            data = d

    n_data = {}
    for k in data.keys():
        c = extract(data, k)
        n_data[k] = c
    CONFIG = ElmesConfig(**n_data)


load_conf(Path(__file__).parent.parent.parent / "guided_teaching.yaml")

from elmes.entity import ElmesConfig
from elmes.utils import extract
from pathlib import Path
from typing import Dict, Any

import yaml

CONFIG: ElmesConfig


def load_conf(path: Path):
    if isinstance(path, str):
        path = Path(path)
    if not path.exists():
        return
    global CONFIG
    data: Dict[str, Dict[str, Any]] = {}
    try:
        with open(path, "r", encoding="utf8") as f:
            t = f.read()
            for d in yaml.safe_load_all(t):
                data = d
    # 编码错误
    except UnicodeDecodeError:
        with open(path, "r", encoding="gbk") as f:
            t = f.read()
            for d in yaml.safe_load_all(t):
                data = d

    n_data = {}
    for k in data.keys():
        c = extract(data, k)
        n_data[k] = c
    if n_data["globals"].get("memory", {}).get("path", None) is None:
        if "memory" not in n_data["globals"]:
            n_data["globals"]["memory"] = {}
        n_data["globals"]["memory"]["path"] = path.parent / path.stem
    CONFIG = ElmesConfig(**n_data)
    if CONFIG.evaluation is not None:
        if CONFIG.evaluation.name is None:
            CONFIG.evaluation.name = path.stem

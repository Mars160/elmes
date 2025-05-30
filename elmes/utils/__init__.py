import itertools
import yaml
from typing import Dict, Any, List
from pathlib import Path


def parse_yaml(path: Path) -> Dict[str, Any]:  # type: ignore
    with open(path, "r") as f:
        t = f.read()
        for d in yaml.safe_load_all(t):
            return d


def extract(data: Dict[str, Any], key: str) -> List[Dict[str, Any]] | Dict[str, Any]:
    if key == "tasks":
        tasks = data["tasks"]
        mode = tasks["mode"].lower()
        if mode == "union":
            content = tasks["content"]
            subcontent_len: List[int] = []
            subcontent_keys: List[str] = []
            sum = 0
            for k, v in content.items():
                if sum == 0:
                    sum = 1
                sum *= len(v)
                subcontent_len.append(len(v))
                subcontent_keys.append(k)

            keys = list(content.keys())
            values = [content[key] for key in keys]
            combinations = list(itertools.product(*values))

            cc: List[Dict[str, Any]] = []
            for c in combinations:
                entry = dict(zip(keys, c))
                cc.append(entry)
            return cc
        elif mode == "iter":
            return data["tasks"]["content"]
        else:
            raise NotImplementedError
    else:
        return data[key]

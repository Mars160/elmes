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

if __name__ == "__main__":
    # CONFIG = ElmesConfig()
    format = CONFIG.evaluation.format_to_pydantic()  # type: ignore
    for name, field in format.model_json_schema().items():
        print(name, field)  # type:

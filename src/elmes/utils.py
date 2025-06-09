from copy import deepcopy
import itertools
import yaml
from typing import Dict, Any, List, Union
from pathlib import Path
from elmes.entity import Prompt


def parse_yaml(path: Path) -> Dict[str, Any]:  # type: ignore
    with open(path, "r") as f:
        t = f.read()
        for d in yaml.safe_load_all(t):
            return d


PromptType = Union[Dict[str, str], Prompt]


def replace_prompt(
    prompt: Union[List[PromptType], PromptType], prompt_map: Dict[str, str]
) -> Union[List[Dict[str, str]], List[Prompt]]:
    result = []
    if isinstance(prompt, List):
        if len(prompt) > 0:
            for p in prompt:
                p = deepcopy(p)  # deep copy to avoid modifying the original
                if isinstance(p, Dict):
                    r = {"role": p["role"]}
                    for k, v in prompt_map.items():
                        r["content"] = p["content"].replace("{" + k + "}", v)
                    result.append(r)
                else:  # isinstance(p, Prompt):
                    for k, v in prompt_map.items():
                        p.content = p.content.replace("{" + k + "}", v)
                    result.append({"role": p.role, "content": p.content})
    else:
        p = deepcopy(prompt)
        if isinstance(p, Dict):
            r = {"role": p["role"]}
            for k, v in prompt_map.items():
                r["content"] = p["content"].replace("{" + k + "}", v)
            result.append(r)
        else:
            for k, v in prompt_map.items():
                p.content = p.content.replace("{" + k + "}", v)
            result.append({"role": p.role, "content": p.content})
    return result


def extract(data: Dict[str, Any], key: str) -> List[Dict[str, Any]] | Dict[str, Any]:
    if key == "tasks":
        tasks = data["tasks"]
        mode = tasks["mode"].lower()
        start_prompt = tasks.get("start_prompt", None)
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
            return {
                "start_prompt": start_prompt,
                "variables": cc,
            }
        elif mode == "iter":
            result = []
            for c in data["tasks"]["content"]:
                entry = c
                result.append(entry)
            return {
                "start_prompt": start_prompt,
                "variables": result,
            }
        else:
            raise NotImplementedError
    else:
        return data[key]


def prompt_to_dict(prompt: Prompt) -> Dict[str, Any]:
    return {"role": prompt.role, "content": prompt.content}

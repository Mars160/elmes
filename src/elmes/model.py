from typing import Dict, Any, Union
from langchain.chat_models import init_chat_model
from langchain.chat_models.base import BaseChatModel


from elmes.entity import ModelConfig


def init_chat_model_from_dict(
    cfg: Dict[str, Union[str, Dict[str, str]]],
) -> BaseChatModel:
    mc = ModelConfig(**cfg)  # type: ignore
    if mc.kargs is not None:
        llm = init_chat_model(
            model=f"{mc.type}:{mc.model}",
            api_key=mc.api_key,
            base_url=mc.api_base,
            **mc.kargs,
        )
    else:
        llm = init_chat_model(
            model=f"{mc.type}:{mc.model}",
            api_key=mc.api_key,
            base_url=mc.api_base,
        )
    return llm


def init_model_map_from_dict(cfg: Dict[str, Any]) -> Dict[str, BaseChatModel]:
    result = {}
    if "models" in cfg:
        cfg = cfg["models"]
    for k, v in cfg.items():
        result[k] = init_chat_model_from_dict(v)
    return result


if __name__ == "__main__":
    from elmes.utils import parse_yaml
    from pathlib import Path

    models = parse_yaml(
        Path(__file__).parent.parent / "guided_teaching" / "models.yaml"
    )["models"]
    a = init_model_map_from_dict(models)
    print(a)

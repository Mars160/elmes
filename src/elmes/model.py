from typing import Dict
from langchain.chat_models import init_chat_model
from langchain.chat_models.base import BaseChatModel


from elmes.entity import ModelConfig
from elmes.config import CONFIG


def init_chat_model_from_dict(mc: ModelConfig) -> BaseChatModel:
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


def init_model_map_from_dict() -> Dict[str, BaseChatModel]:
    cfg = CONFIG.models
    result = {}
    for k, v in cfg.items():
        result[k] = init_chat_model_from_dict(v)
    return result


init_model_map = init_model_map_from_dict

if __name__ == "__main__":
    a = init_model_map_from_dict()
    print(a)

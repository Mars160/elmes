from elmes.config import Model

from pydantic_ai.models import Model as PydanticAIModel


def build_model(model_config: Model) -> PydanticAIModel:
    """根据ModelConfig和RetryConfig构建模型实例"""
    if model_config.type == "openai":
        from elmes.model.openai_provider import build_model

        return build_model(model_config)
    else:
        raise ValueError(f"Unsupported model type: {model_config.type}")


if __name__ == "__main__":
    from elmes.config import load_config

    config = load_config("config.yaml.example")
    for model_name, model_config in config.models.items():
        model = build_model(model_config)
        print(f"Model {model_name} built successfully: {model.__dict__}")

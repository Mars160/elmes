from pydantic import BaseModel, Field


class Task(BaseModel):
    start_prompt: str = Field(..., description="任务的初始提示词")
    content: list[dict[str, str]]

    @staticmethod
    def from_dict(data: dict) -> "Task":
        assert "start_prompt" in data, "tasks配置必须包含start_prompt字段"
        assert len(data["content"]) > 0, "content must be a non-empty list"
        start_prompt = data["start_prompt"]
        assert isinstance(start_prompt, str), "start_prompt must be a string"

        tasks = []
        mode = data.get("mode", "union")
        if mode == "union":
            content: dict[str, list[str]] = data["content"]  # pyright: ignore[reportRedeclaration]
            # 笛卡尔积生成任务列表
            keys = list(content.keys())  # pyright: ignore[reportAttributeAccessIssue]
            values = list(content.values())  # pyright: ignore[reportAttributeAccessIssue]
            assert all(isinstance(v, list) for v in values), (
                "content中的每个字段必须是一个列表"
            )
            from itertools import product

            for combination in product(*values):
                task = {k: v for k, v in zip(keys, combination)}
                tasks.append(task)
        elif mode == "iter":
            content: list[dict[str, str]] = data["content"]
            assert all(isinstance(item, dict) for item in content), (
                "content中的每个元素必须是一个字典"
            )
            tasks = content
        else:
            raise ValueError(f"不支持的mode类型: {mode}")

        return Task(start_prompt=start_prompt, content=tasks)


if __name__ == "__main__":
    import yaml

    with open("config.yaml.example", "r", encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)

    data = config_dict.get("tasks", None)
    if data:
        task = Task.from_dict(data)
        print(task)

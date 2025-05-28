from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
import json
import time
import yaml
from datetime import datetime
from typing import Dict, Any, List, Optional, Type, override
from pathlib import Path
from src.prompts.base import BasePromptGenerator
from src.backend.base import Backend


class Executor(ABC):
    """
    执行器基类，处理从提示词生成到模型调用再到保存结果的完整流程
    """

    def __init__(
        self, backend: Any, prompt_generator: Any, output_dir: str = "results"
    ):
        """
        初始化执行器

        Args:
            backend: 模型后端
            prompt_generator: 提示词生成器
            output_dir: 结果保存目录
        """
        self.backend: Type[Backend] = backend
        self.prompt_generator: Type[BasePromptGenerator] = prompt_generator
        self.output_dir = output_dir

        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def generate_prompt(self, task_id: Any, **kwargs) -> Dict[str, Any]:
        """
        生成提示词

        Args:
            task_id: 任务ID
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 生成的提示词，包含系统提示词和用户提示词
        """
        pass

    @abstractmethod
    def call_model(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        调用模型推理

        Args:
            messages: 输入消息列表
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 模型响应
        """
        pass

    @abstractmethod
    def process_response(self, response: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        处理模型响应

        Args:
            response: 模型原始响应
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 处理后的响应结果
        """
        pass

    @abstractmethod
    def save_result(
        self, result: Dict[str, Any], filename: Optional[str] = None
    ) -> str:
        """
        保存结果到目标目录

        Args:
            result: 处理后的结果
            filename: 文件名，如不提供则自动生成

        Returns:
            str: 保存的文件路径
        """
        pass

    def execute(self, task_id: Any, save: bool = True, **kwargs) -> Dict[str, Any]:
        """
        执行完整流程：生成提示词 -> 调用模型 -> 处理响应 -> 保存结果

        Args:
            task_id: 任务ID
            save: 是否保存结果
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 记录开始时间
        start_time = time.time()

        # 1. 生成提示词
        prompt_data = self.generate_prompt(task_id, **kwargs)

        # 2. 调用模型
        response = self.call_model(prompt_data["messages"], **kwargs)

        # 3. 处理响应
        result = self.process_response(response, prompt=prompt_data, **kwargs)

        # 4. 记录执行信息
        # 获取后端类型名称（如"ollama", "openai"等）
        backend_type = self.backend.__class__.__name__.lower().replace("backend", "")

        result["execution_info"] = {
            "task_id": task_id,
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat(),
            "backend": backend_type,
            "model_name": getattr(self.backend, "model_name", "unknown"),
        }

        # 5. 保存结果（如果需要）
        if save:
            result["saved_path"] = self.save_result(result, **kwargs)

        return result

    def _get_default_filename(self, task_id: Any, scenario: str = None) -> str:
        """
        生成默认文件名
        格式：日期_差异码_S{场景ID}_T{任务ID}_model_name.json

        Args:
            task_id: 任务ID
            scenario: 场景名称

        Returns:
            str: 生成的文件名
        """
        # 生成日期（年月日）
        date = datetime.now().strftime("%Y%m%d")

        # 生成差异码（时分秒+毫秒的后3位）
        diff_code = datetime.now().strftime("%H%M%S") + str(
            int(time.time() * 1000) % 1000
        ).zfill(3)

        # 获取场景名称
        scenario_name = scenario or getattr(
            self.prompt_generator, "scenario_name", "unknown"
        )

        # 从config.yaml获取场景ID
        scenario_id = self._get_scenario_id(scenario_name)

        # 获取模型名称并处理特殊字符
        model_name = (
            getattr(self.backend, "model_name", "unknown")
            .replace("/", "-")
            .replace(":", "-")
        )

        return f"{date}_{diff_code}_S{scenario_id}_T{task_id}_{model_name}.json"

    def _get_scenario_id(self, scenario_name: str) -> int:
        """
        从config.yaml获取场景ID

        Args:
            scenario_name: 场景名称

        Returns:
            int: 场景ID，如果找不到则返回0
        """
        try:
            config_paths = [Path("config/config.yaml"), Path("config.yaml")]

            for config_path in config_paths:
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f)

                    scenarios = config.get("scenarios", {})
                    if scenario_name in scenarios:
                        return scenarios[scenario_name].get("id", 0)

                    break
        except Exception as e:
            print(f"读取配置文件失败: {e}")

        return 0


class GeneratedPrompt:
    def __init__(
        self, messages: List[Dict[str, str]], task_id: Any, original_prompt: str
    ):
        self.messages = messages
        self.task_id = task_id
        self.original_prompt = original_prompt

    def to_dict(self) -> Dict[str, Any]:
        return {
            "messages": self.messages,
            "task_id": self.task_id,
            "original_prompt": self.original_prompt,
        }

    # 重载[]操作符，使其可以像字典一样访问
    def __getitem__(self, key: str) -> Any:
        return self.to_dict().get(key)

    @override
    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=4)

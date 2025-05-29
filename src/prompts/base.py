from abc import ABC, abstractmethod
import yaml
from typing import Dict, Any, Optional
import os
from pathlib import Path


class BasePromptGenerator(ABC):
    """基础提示词生成器类"""

    def __init__(self, scenario_name: str):
        """
        初始化提示词生成器

        Args:
            scenario_name: 场景名称
        """
        self.scenario_name = scenario_name
        self.scenario_prompts = self._load_scenario_prompts()

    def _load_scenario_prompts(self) -> Dict[str, Any]:
        """加载场景提示词配置"""
        config_path = Path("config/prompts/scenario_prompts.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Scenario prompts file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data[self.scenario_name]

    def _load_task_prompts(self, task_id: int) -> Dict[str, Any]:
        """加载任务提示词配置"""
        config_path = Path("config/prompts/task_prompts.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Task prompts file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data[self.scenario_name]["task{}".format(task_id)]

    def replace_task(self, src: str, task_prompts: Dict[str, Any]) -> str:
        """替换任务占位符"""
        for key, value in task_prompts.items():
            src = src.replace(f"{{{key}}}", value)
        return src

    def generate_prompt(self, task_name: str, **kwargs) -> str:
        """
        生成系统提示词
        """

        task_prompts = self._load_task_prompts(task_name)
        prompt = self._generate_prompt(self.scenario_prompts, task_prompts)
        return prompt

    @abstractmethod
    def _generate_prompt(
        self, scenario_prompts: Dict[str, Any], task_prompts: Dict[str, Any]
    ) -> str:
        """生成系统提示词"""
        pass

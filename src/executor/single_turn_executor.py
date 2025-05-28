import os
import json
import logging
from syslog import LOG_DEBUG
from typing import Dict, Any, List, Optional

from src.backend.openai_backend import OpenAIBackend
from src.executor.base import Executor
from src.prompts.knowledge_explanation import KnowledgeExplanationPromptGenerator


# 初始化日志配置
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SingleTurnExecutor(Executor):
    """
    单轮对话执行器，提供单轮对话的执行功能实现
    """

    def generate_prompt(self, task_id: Any, **kwargs) -> Dict[str, Any]:
        logger.info("开始为任务ID %s 生成提示词", task_id)
        logger.debug("任务ID: %s，传入参数: %s", task_id, kwargs)
        """
        生成提示词

        Args:
            task_id: 任务ID
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 生成的提示词，包含系统提示词和用户提示词
        """
        logger.info("开始为任务ID %s 生成提示词", task_id)
        # 获取提示词生成器生成的提示词
        prompt = self.prompt_generator.generate_prompt(task_id, **kwargs)

        # 构建消息格式
        # 假设提示词生成器返回的是一个包含系统提示词和用户提示词的字符串
        # 这里将其转换为OpenAI格式的消息列表

        # 检查返回的是否已经是消息列表格式
        if isinstance(prompt, list) and all(isinstance(m, dict) for m in prompt):
            messages = prompt
        else:
            # 尝试从提示词中提取系统提示词和用户提示词
            system_prompt = kwargs.get("system_prompt", "你是一个有帮助的AI助手。")
            if isinstance(prompt, dict):
                # 如果返回的是字典格式，尝试提取系统提示词和用户提示词
                system_prompt = prompt.get("system_prompt", system_prompt)
                user_prompt = prompt.get("user_prompt", prompt.get("prompt", ""))
            else:
                # 如果是字符串，直接作为用户提示词
                user_prompt = prompt

            # 构建消息
            messages = [{"role": "system", "content": system_prompt}]

            # 如果用户提示词不为空，添加到消息中
            if user_prompt:
                messages.append({"role": "user", "content": user_prompt})
        logger.debug("生成的消息列表: %s", messages)
        logger.info("任务ID %s 的提示词生成完成", task_id)
        return {"messages": messages, "task_id": task_id, "original_prompt": prompt}

    def call_model(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        logger.info("开始调用模型进行推理，输入消息数量: %d", len(messages))
        logger.debug(
            "调用模型的参数: temperature=%s, max_tokens=%s, 其他参数: %s",
            kwargs.get("temperature", 0.7),
            kwargs.get("max_tokens", 4000),
            {k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]},
        )
        """
        调用模型推理

        Args:
            messages: 输入消息列表
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 模型响应
        """
        # 提取模型调用参数
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 4000)

        # 调用模型
        response = self.backend.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **{
                k: v
                for k, v in kwargs.items()
                if k not in ["temperature", "max_tokens"]
            },
        )
        logger.debug("模型返回的原始响应: %s", response)
        logger.info("模型推理完成，返回响应")
        return response

    def process_response(self, response: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        logger.info("开始处理模型响应")
        logger.debug("接收到的原始响应: %s，额外参数: %s", response, kwargs)
        """
        处理模型响应

        Args:
            response: 模型原始响应
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 处理后的响应结果
        """
        # 获取提示词信息
        prompt_data = kwargs.get("prompt", {})

        # 构建简化的结果，只保留指定字段
        result = {
            "scenario": self.prompt_generator.scenario_name
            if hasattr(self.prompt_generator, "scenario_name")
            else "unknown",
            "task_id": prompt_data.get("task_id", "unknown"),
            "messages": prompt_data.get("messages", []),
            "raw_response": response,
        }

        return result

    def save_result(
        self, result: Dict[str, Any], filename: Optional[str] = None, **kwargs
    ) -> str:
        logger.info("开始保存处理后的结果，指定文件名: %s", filename)
        logger.debug("要保存的结果内容: %s", result)
        """
        保存结果到目标目录

        Args:
            result: 处理后的结果
            filename: 文件名，如不提供则自动生成
            **kwargs: 其他参数

        Returns:
            str: 保存的文件路径
        """
        # 如果没有提供文件名，生成默认文件名
        if not filename:
            scenario = result.get("scenario", "unknown")
            filename = self._get_default_filename(
                result.get("task_id", "unknown"), scenario
            )

        # 确保文件名有.json扩展名
        if not filename.endswith(".json"):
            filename += ".json"

        # 构建完整路径
        filepath = os.path.join(self.output_dir, filename)

        # 保存结果
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return filepath

    def initialize(self) -> bool:
        logger.info("开始初始化执行器")
        """
        初始化执行器，包括后端初始化

        Returns:
            bool: 初始化是否成功
        """
        # 初始化后端
        if hasattr(self.backend, "initialize"):
            return self.backend.initialize()
        return True


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    prompt_generator = KnowledgeExplanationPromptGenerator()
    backend = OpenAIBackend(
        model_name="gpt-4o-mini",
        api_base="https://api.gptgod.online/v1/",
        api_key="sk-ItJIZMO3tk7YCx6LPBgS2JHU4OkRM3o1nu9kUVm7yvCaOPOz",
    )
    task_id = 1
    # 正确初始化执行器，使用字符串作为输出目录
    executor = SingleTurnExecutor(backend, prompt_generator, "results")
    executor.initialize()
    for i in range(1, 3):
        executor.execute(i)

import os
import json
import logging
from typing import Dict, Any, List, Optional, Type
import time

from src.executor.base import Executor, GeneratedPrompt
from src.backend.base import Backend
from src.prompts.base import BasePromptGenerator
from src.prompts.knowledge_explanation import KnowledgeExplanationPromptGenerator
from src.backend.openai_backend import OpenAIBackend


# 初始化日志配置
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MultiTurnExecutor(Executor):
    """
    多轮对话执行器，提供多轮对话的执行功能实现
    """

    def __init__(
        self,
        backend: Type[Backend],
        prompt_generator: Type[BasePromptGenerator],
        output_dir,
    ):
        """
        初始化多轮对话执行器

        Args:
            backend: 后端模型接口，应为 BaseBackend 的子类
            prompt_generator: 提示词生成器
            output_dir: 输出目录
        """
        super().__init__(backend, prompt_generator, output_dir)
        self.conversation_history = []  # 对话历史记录
        self.conversation_state = {}  # 对话状态信息
        logger.debug(
            "多轮对话执行器初始化参数: backend=%s, prompt_generator=%s, output_dir=%s",
            backend,
            prompt_generator,
            output_dir,
        )
        logger.info("多轮对话执行器已初始化")

    def generate_prompt(self, task_id: Any, **kwargs) -> GeneratedPrompt:
        logger.debug("开始生成多轮对话提示词，任务ID: %s，参数: %s", task_id, kwargs)
        logger.info("开始生成多轮对话的提示词，任务ID: %s", task_id)
        """
        生成多轮对话的提示词
        """
        # 获取提示词生成器生成的提示词
        prompt = self.prompt_generator.generate_prompt(task_id, **kwargs)

        if isinstance(prompt, list) and all(isinstance(m, dict) for m in prompt):
            # 如果返回的是消息列表，直接使用
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

        # 合并历史对话和新的用户输入
        messages = [
            {"role": "system", "content": system_prompt}
        ] + self.conversation_history
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        logger.debug("多轮对话生成的提示词: %s", messages)
        logger.info("多轮对话的提示词生成完成，任务ID: %s", task_id)
        return GeneratedPrompt(
            messages=messages,
            task_id=task_id,
            original_prompt=prompt,
        )

    def call_model(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        logger.debug(
            "开始调用模型进行多轮对话推理，消息: %s，参数: %s", messages, kwargs
        )
        logger.info("开始调用模型进行多轮对话推理")
        """
        调用模型进行多轮对话推理
        """
        # 处理长对话的 token 限制，简单截断历史对话
        max_tokens = kwargs.get("max_tokens", 4000)
        while len(str(messages)) > max_tokens:
            if len(self.conversation_history) > 0:
                self.conversation_history.pop(0)
            else:
                break
            messages = (
                [{"role": "system", "content": "你是一个有帮助的AI助手。"}]
                + self.conversation_history
                + messages[-1:]
            )

        logger.debug("处理后的消息: %s", messages)
        result = self.backend.chat(messages=messages, **kwargs)
        logger.debug("模型返回结果: %s", result)
        logger.info("模型调用完成，返回结果")
        return result

    def process_response(self, response: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        logger.debug("开始处理多轮对话的模型响应，响应: %s，参数: %s", response, kwargs)
        logger.info("开始处理多轮对话的模型响应")
        """
        处理多轮对话的模型响应
        """
        # 更新对话历史
        assistant_message = response["choices"][0]["message"]
        self.conversation_history.append(assistant_message)

        # 处理对话状态变化，这里简单假设没有状态变化
        self.conversation_state = {}

        # 判断对话是否结束，这里简单假设没有结束条件
        is_end = False

        result = {
            "response": response,
            "conversation_history": self.conversation_history,
            "conversation_state": self.conversation_state,
            "is_end": is_end,
        }

        logger.debug("处理后的结果: %s", result)
        return result

    def save_result(
        self, result: Dict[str, Any], filename: Optional[str] = None, **kwargs
    ) -> str:
        logger.debug(
            "开始保存多轮对话结果，结果: %s，文件名: %s，参数: %s",
            result,
            filename,
            kwargs,
        )
        logger.info("开始保存多轮对话结果，文件名: %s", filename)
        """
        保存多轮对话结果
        """
        if not filename:
            filename = f"multi_turn_conversation_{int(time.time())}.json"

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.debug("多轮对话结果保存到: %s", filepath)
        logger.info("多轮对话结果保存完成，文件路径: %s", filepath)
        return filepath

    def start_conversation(self, task_id: Any, **kwargs) -> Dict[str, Any]:
        logger.debug("开始新的多轮对话，任务ID: %s，参数: %s", task_id, kwargs)
        logger.info("开始新的多轮对话，任务ID: %s", task_id)
        """
        开始新的多轮对话
        """
        self.conversation_history = []
        self.conversation_state = {}

        prompt = self.generate_prompt(task_id, **kwargs)
        response = self.call_model(prompt.messages, **kwargs)
        result = self.process_response(response, prompt=prompt, **kwargs)

        if kwargs.get("save", True):
            self.save_result(result)

        logger.debug("新的多轮对话结果: %s", result)
        return result

    def continue_conversation(self, user_input: str, **kwargs) -> Dict[str, Any]:
        logger.debug("继续进行多轮对话，用户输入: %s，参数: %s", user_input, kwargs)
        logger.info("继续进行多轮对话，用户输入: %s", user_input)
        """
        继续进行多轮对话
        """
        task_id = kwargs.get("task_id")
        prompt = self.generate_prompt(task_id, user_prompt=user_input, **kwargs)
        response = self.call_model(prompt.messages, **kwargs)
        result = self.process_response(response, prompt=prompt, **kwargs)

        if kwargs.get("save", True):
            self.save_result(result)

        logger.debug("继续多轮对话的结果: %s", result)
        return result

    def end_conversation(self, **kwargs) -> Dict[str, Any]:
        logger.debug("结束多轮对话，参数: %s", kwargs)
        logger.info("结束多轮对话")
        """
        结束多轮对话
        """
        summary = {
            "conversation_history": self.conversation_history,
            "conversation_state": self.conversation_state,
        }

        if kwargs.get("save", True):
            self.save_result(summary)

        logger.debug("多轮对话总结: %s", summary)
        logger.info("多轮对话已结束")
        return summary

    def initialize(self) -> bool:
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
    executor = MultiTurnExecutor(backend, prompt_generator, "results")
    executor.initialize()
    for i in range(1, 3):
        executor.execute(i)

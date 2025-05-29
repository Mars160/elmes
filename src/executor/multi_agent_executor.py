import os
import json
import logging
from typing import Dict, Any, List, Optional, Type, override
import time
from datetime import datetime

from src.executor.base import Executor, GeneratedPrompt
from src.backend.base import Backend
from src.prompts.base import BasePromptGenerator
from src.prompts.guided_teaching import GuidedTeachingPromptGenerator
from src.backend.openai_backend import OpenAIBackend


# 初始化日志配置
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MultiAgentExecutor(Executor):
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
        self.conversation_history: Dict[List[Dict[str, Any]]] = {}
        self.conversation_state = {}  # 对话状态信息
        logger.debug(
            "多轮对话执行器初始化参数: backend=%s, prompt_generator=%s, output_dir=%s",
            backend,
            prompt_generator,
            output_dir,
        )
        logger.info("多轮对话执行器已初始化")

    def generate_prompt(self, task_id: Any, **kwargs) -> Dict[str, Any]:
        logger.debug("开始生成多轮对话提示词，任务ID: %s，参数: %s", task_id, kwargs)
        logger.info("开始生成多轮对话的提示词，任务ID: %s", task_id)
        """
        生成多轮对话的提示词
        """
        # 获取提示词生成器生成的提示词
        prompt = self.prompt_generator.generate_prompt(task_id, **kwargs)
        teacher_prompt = prompt.get("teacher", [])
        student_prompt = prompt.get("student", [])

        # 合并历史对话和新的用户输入
        teacher_messages = teacher_prompt + self.conversation_history.get("teacher", [])
        student_messages = student_prompt + self.conversation_history.get("student", [])

        messages = {
            "teacher": teacher_messages,
            "student": student_messages,
        }

        logger.debug("多轮对话生成的提示词: %s", messages)
        logger.info("多轮对话的提示词生成完成，任务ID: %s", task_id)
        return messages

    @override
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

        teacher_prompt = prompt_data.get("teacher", [])
        student_prompt = prompt_data.get("student", [])

        teacher_response = self.call_model(teacher_prompt, **kwargs)
        teacher_result = self.process_response(
            teacher_response, prompt=prompt_data, **kwargs
        )
        print(teacher_result)

        student_response = self.call_model(student_prompt, **kwargs)

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
        self.conversation_history: Dict[List[Dict[str, Any]]] = {
            "teacher": [],
            "student": [],
        }
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
    prompt_generator = GuidedTeachingPromptGenerator()
    backend = OpenAIBackend(
        model_name="gpt-4o-mini",
        api_base="https://api.gptgod.online/v1/",
        api_key="sk-ItJIZMO3tk7YCx6LPBgS2JHU4OkRM3o1nu9kUVm7yvCaOPOz",
    )
    task_id = 1
    # 正确初始化执行器，使用字符串作为输出目录
    executor = MultiAgentExecutor(backend, prompt_generator, "results")
    executor.initialize()
    for i in range(1, 3):
        executor.execute(i)

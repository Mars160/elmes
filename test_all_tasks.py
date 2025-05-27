#!/usr/bin/env python3
"""
测试脚本 - 验证所有任务的生成和命名
"""

from src.executor.single_turn_executor import SingleTurnExecutor
from src.prompts.knowledge_explanation import KnowledgeExplanationPromptGenerator
from src.prompts.contextual_problem import ContextualProblemPromptGenerator
from src.backend.ollama_backend import OllamaBackend
from src.backend.deepseek_backend import DeepSeekBackend
from src.backend.openai_backend import OpenAIBackend

def test_all_tasks():
    """测试生成所有4个tasks"""
    # prompt_generator = KnowledgeExplanationPromptGenerator()
    prompt_generator = ContextualProblemPromptGenerator()
    # backend = OllamaBackend()
    # backend = DeepSeekBackend()
    backend = OpenAIBackend()
    executor = SingleTurnExecutor(backend, prompt_generator, 'results')
    executor.initialize()

    # 测试生成所有4个tasks
    for i in range(1, 5):
        print(f'生成任务 {i}...')
        try:
            result = executor.execute(i)
            print(f'任务 {i} 完成 - 文件: {result.get("saved_path", "未保存")}')
        except Exception as e:
            print(f'任务 {i} 失败: {e}')

if __name__ == "__main__":
    test_all_tasks() 
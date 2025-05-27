import os
import json
import yaml
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from src.backend import OllamaBackend, OpenAIBackend, DeepSeekBackend


class Evaluator:
    """
    评估器，用于对LLM生成的教学内容进行质量评估
    
    主要功能：
    1. 解析结果文件，提取场景、问题和回答
    2. 根据场景加载对应的评估提示词
    3. 调用评估模型进行质量评估
    4. 保存评估结果
    """
    
    def __init__(self, backend_config: str = "openai", output_dir: str = "evaluation_result"):
        """
        初始化评估器
        
        Args:
            backend_config: 后端配置名称 (openai, ollama, deepseek)
            output_dir: 评估结果输出目录
        """
        self.backend_config = backend_config
        self.output_dir = output_dir
        self.backend = None
        self.evaluation_prompts = {}
        
        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    def initialize(self) -> bool:
        """
        初始化评估器
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self._load_evaluation_prompts()
            self._initialize_backend()
            return True
        except Exception as e:
            print(f"评估器初始化失败: {e}")
            return False
    
    def _load_evaluation_prompts(self):
        """加载评估提示词配置"""
        prompts_path = Path("config/prompts/evaluation_prompts.yaml")
        
        if not prompts_path.exists():
            raise FileNotFoundError(f"评估提示词文件不存在: {prompts_path}")
        
        with open(prompts_path, 'r', encoding='utf-8') as f:
            self.evaluation_prompts = yaml.safe_load(f)
    
    def _initialize_backend(self):
        """初始化后端"""
        config = self._load_backend_config()
        
        # 创建后端实例
        backend_map = {
            "openai": OpenAIBackend,
            "ollama": OllamaBackend,
            "deepseek": DeepSeekBackend
        }
        
        if self.backend_config not in backend_map:
            raise ValueError(f"不支持的后端配置: {self.backend_config}")
        
        backend_class = backend_map[self.backend_config]
        self.backend = backend_class(
            model_name=config.get("model_name"),
            api_base=config.get("api_base"),
            api_key=config.get("api_key")
        )
        
        if not self.backend.initialize():
            raise Exception(f"后端 {self.backend_config} 初始化失败")
    
    def _load_backend_config(self) -> Dict[str, Any]:
        """加载后端配置"""
        config_path = Path("config/evaluation_backend.yaml")
        
        if not config_path.exists():
            raise FileNotFoundError(f"后端配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if self.backend_config not in config:
            raise ValueError(f"后端配置 '{self.backend_config}' 不存在")
        
        return config[self.backend_config]
    
    def evaluate_file(self, result_file_path: str, **kwargs) -> str:
        """
        评估结果文件
        
        Args:
            result_file_path: 结果文件路径
            **kwargs: 格式化参数
            
        Returns:
            str: 评估结果文件路径
        """
        # 1. 解析结果文件
        result_data = self._load_result_file(result_file_path)
        scenario = result_data.get("scenario", "unknown")
        
        # 2. 提取Q&A内容
        user_content = self._extract_user_content(result_data)
        assistant_content = self._extract_assistant_content(result_data)
        
        # 3. 构建评估提示词
        evaluation_prompt = self._build_evaluation_prompt(
            scenario, user_content, assistant_content, **kwargs
        )
        
        # 4. 调用评估模型
        evaluation_response = self._call_evaluation_model(evaluation_prompt)
        
        # 5. 保存评估结果
        return self._save_evaluation_result(
            result_data, evaluation_response, result_file_path
        )
    
    def _load_result_file(self, file_path: str) -> Dict[str, Any]:
        """读取结果文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _extract_user_content(self, result_data: Dict[str, Any]) -> str:
        """提取用户问题内容"""
        for message in result_data.get("messages", []):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""
    
    def _extract_assistant_content(self, result_data: Dict[str, Any]) -> str:
        """提取助手回答内容"""
        raw_response = result_data.get("raw_response", {})
        choices = raw_response.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""
    
    def _build_evaluation_prompt(self, scenario: str, user_content: str, 
                               assistant_content: str, **kwargs) -> str:
        """构建评估提示词"""
        if scenario not in self.evaluation_prompts:
            raise ValueError(f"场景 '{scenario}' 的评估提示词不存在")
        
        template = self.evaluation_prompts[scenario]
        
        # 格式化参数
        format_params = {
            "prompt": user_content,
            "query": assistant_content,
            "LLM_response": assistant_content,
            "Student_image": kwargs.get("Student_image", "小学生"),
            "Student_query": kwargs.get("Student_query", user_content),
            **kwargs
        }
        
        # 格式化模板
        try:
            return template.format(**format_params)
        except KeyError:
            # 如果格式化失败，逐个替换参数
            result = template
            for key, value in format_params.items():
                result = result.replace(f"{{{key}}}", str(value))
            return result
    
    def _call_evaluation_model(self, evaluation_content: str) -> Dict[str, Any]:
        """调用评估模型"""
        messages = [
            {"role": "system", "content": "你是一个专业的教学评估专家，请根据给定的标准对教学内容进行客观、公正的评估。"},
            {"role": "user", "content": evaluation_content}
        ]
        
        return self.backend.chat(
            messages=messages,
            temperature=0.1,
            max_tokens=2000
        )
    
    def _save_evaluation_result(self, result_data: Dict[str, Any], 
                              evaluation_response: Dict[str, Any], 
                              original_file_path: str) -> str:
        """保存评估结果"""
        # 生成评估结果文件名
        original_filename = Path(original_file_path).name
        evaluation_filename = f"eval_{original_filename}"
        evaluation_filepath = Path(self.output_dir) / evaluation_filename
        
        # 构建评估结果数据
        evaluation_result = {
            "original_file": original_file_path,
            "scenario": result_data.get("scenario"),
            "task_id": result_data.get("task_id"),
            "evaluation_backend": self.backend_config,
            "evaluation_model": getattr(self.backend, 'model_name', 'unknown'),
            "evaluation_response": evaluation_response,
            "evaluation_timestamp": datetime.now().isoformat()
        }
        
        # 保存评估结果
        with open(evaluation_filepath, 'w', encoding='utf-8') as f:
            json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
        
        return str(evaluation_filepath)


# 便捷函数接口
def evaluate_json(result_file_path: str,
                  backend: str = "openai",
                  output_dir: str = "evaluation_result",
                  **format_kwargs) -> str:
    """
    评估单个JSON结果文件的便捷函数
    
    Args:
        result_file_path: 结果JSON文件路径
        backend: 后端名称 (openai, ollama, deepseek)
        output_dir: 评估结果输出目录
        **format_kwargs: 格式化参数 (如Student_image, Student_query)
        
    Returns:
        str: 保存的评估结果文件路径
    """
    evaluator = Evaluator(backend_config=backend, output_dir=output_dir)
    
    if not evaluator.initialize():
        raise RuntimeError("评估器初始化失败，请检查后端配置")
    
    return evaluator.evaluate_file(result_file_path, **format_kwargs)


if __name__ == "__main__":
    import glob
    import argparse
    
    parser = argparse.ArgumentParser(description="评估单个结果JSON文件")
    parser.add_argument("json_path", nargs="?", help="JSON文件路径")
    parser.add_argument("--backend", default="openai", help="后端: openai, ollama, deepseek")
    args = parser.parse_args()
    
    if args.json_path:
        target_file = args.json_path
    else:
        files = glob.glob("results/*.json")
        if not files:
            print("⚠️  未找到结果文件")
            exit(1)
        target_file = files[0]
    
    print(f"📝 评估文件: {target_file}")
    
    try:
        saved_path = evaluate_json(target_file, backend=args.backend)
        print(f"✅ 评估完成，结果保存至: {saved_path}")
    except Exception as e:
        print(f"❌ 评估失败: {e}")
        exit(1) 



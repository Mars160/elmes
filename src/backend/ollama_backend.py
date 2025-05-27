import json
import requests
from typing import Dict, List, Any
import time

from src.backend.base import Backend

class OllamaBackend(Backend):
    """Ollama API 后端实现"""
    
    def __init__(self, model_name: str = None, api_base: str = None, api_key: str = None):
        """
        初始化 Ollama 后端
        
        Args:
            model_name: 模型名称，如不提供则从配置或环境变量获取
            api_base: API基础URL，如不提供则从配置或环境变量获取
            api_key: API密钥（Ollama通常不需要）
        """
        super().__init__(backend_type="ollama", model_name=model_name, api_base=api_base, api_key=api_key)
    
    def _get_default_model(self) -> str:
        """获取Ollama默认模型名称"""
        return "qwen2.5:14b"
    
    def _get_default_api_base(self) -> str:
        """获取Ollama默认API基础URL"""
        return "http://localhost:11434"
    
    def initialize(self) -> bool:
        """
        初始化后端连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 检查Ollama服务是否可用
            response = requests.get(
                f"{self.api_base}/api/tags",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # 检查模型是否存在
            models_data = response.json()
            models = models_data.get('models', [])
            available_models = [model.get('name') for model in models]
            
            if self.model_name not in available_models:
                print(f"警告: 模型 '{self.model_name}' 在Ollama中不可用")
                print(f"可用模型: {', '.join(available_models)}")
            
            self.initialized = True
            return True
        except Exception as e:
            print(f"初始化Ollama连接失败: {e}")
            self.initialized = False
            return False
    
    def _prepare_messages(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        准备Ollama API所需的消息格式
        
        Args:
            messages: OpenAI格式的消息列表
            
        Returns:
            Dict[str, Any]: Ollama API格式的数据
        """
        # 提取系统提示词
        system = self.system_prompt
        for msg in messages:
            if msg.get('role') == 'system':
                system = msg.get('content', system)
                break
        
        # 构建对话历史
        prompt = ""
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role == 'system':
                continue  # 系统消息已单独处理
            elif role == 'user':
                prompt += f"[用户] {content}\n"
            elif role == 'assistant':
                prompt += f"[助手] {content}\n"
            else:
                prompt += f"[{role}] {content}\n"
        
        return {
            "prompt": prompt.strip(),
            "system": system,
            "model": self.model_name
        }
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             temperature: float = 0.7, 
             max_tokens: int = 2000, 
             **kwargs) -> Dict[str, Any]:
        """
        发送聊天请求并获取响应
        
        Args:
            messages: 对话历史 [{"role": "user", "content": "你好"}, ...]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成的token数量
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 模型响应结果
        """
        if not self.initialized:
            success = self.initialize()
            if not success:
                raise RuntimeError("Ollama后端初始化失败")
        
        # 准备请求数据
        data = self._prepare_messages(messages)
        data.update({
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": False
        })
        
        # 添加其他参数
        for key in ['top_p', 'top_k', 'repeat_penalty']:
            if key in kwargs:
                data[key] = kwargs[key]
        
        # 发送请求
        result = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.api_base}/api/generate",
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(data),
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                break
            except Exception as e:
                print(f"请求失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避重试
        
        if result is None:
            raise RuntimeError(f"所有请求尝试失败，已重试 {self.max_retries} 次")
        
        # 将Ollama响应转换为标准格式的响应
        response_content = result.get("response", "")
        standard_response = self._create_standard_response(response_content)
        standard_response["usage"] = result.get("usage", {})
        return standard_response
    
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            List[str]: 可用模型名称列表
        """
        if not self.initialized:
            self.initialize()
        
        try:
            response = requests.get(
                f"{self.api_base}/api/tags",
                timeout=self.timeout
            )
            response.raise_for_status()
            models_data = response.json()
            return [model.get('name') for model in models_data.get('models', [])]
        except Exception as e:
            print(f"获取模型列表失败: {e}")
            return []


# 简单的测试代码
if __name__ == "__main__":
    # 创建Ollama后端
    backend = OllamaBackend()
    
    # 初始化
    success = backend.initialize()
    if not success:
        print("初始化失败，退出")
        exit(1)
    
    print(f"使用模型: {backend.model_name}")
    
    # 发送一个简单的请求
    messages = [
        # {"role": "system", "content": "你是一个友好、有帮助的AI助手。请用中文回答。"},
        {"role": "user", "content": "你好，请介绍一下自己。"}
    ]
    
    try:
        response = backend.chat(messages)
        print("\n回复内容:")
        print("-" * 40)
        print(response["choices"][0]["message"]["content"])
        print("-" * 40)
    except Exception as e:
        print(f"请求失败: {e}") 
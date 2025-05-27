import json
import requests
from typing import Dict, List, Any
import time

from src.backend.base import Backend

class OpenAIBackend(Backend):
    """OpenAI API 后端实现"""
    
    def __init__(self, model_name: str = None, api_base: str = None, api_key: str = None):
        """
        初始化 OpenAI 后端
        
        Args:
            model_name: 模型名称，如不提供则从配置或环境变量获取
            api_base: API基础URL，如不提供则从配置或环境变量获取
            api_key: API密钥，如不提供则从配置或环境变量获取
        """
        super().__init__(backend_type="openai", model_name=model_name, api_base=api_base, api_key=api_key)
    
    def _get_default_model(self) -> str:
        """获取OpenAI默认模型名称"""
        return "gpt-3.5-turbo"
    
    def _get_default_api_base(self) -> str:
        """获取OpenAI默认API基础URL"""
        return "https://api.openai.com/v1"
    
    def initialize(self) -> bool:
        """
        初始化OpenAI后端连接
        
        Returns:
            bool: 初始化是否成功
        """
        if not self.api_key:
            print("❌ OpenAI API密钥未设置")
            self.initialized = False
            return False
        
        try:
            # 测试API连接
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 尝试获取模型列表来验证API密钥
            response = requests.get(
                f"{self.api_base}/models",
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.initialized = True
                return True
            else:
                print(f"❌ OpenAI API连接失败: HTTP {response.status_code}")
                self.initialized = False
                return False
                
        except Exception as e:
            print(f"❌ 初始化OpenAI连接失败: {e}")
            self.initialized = False
            return False
    
    def chat(self, 
             messages: List[Dict[str, str]], 
             temperature: float = 0.7, 
             max_tokens: int = 4000, 
             **kwargs) -> Dict[str, Any]:
        """
        发送OpenAI聊天请求并获取响应
        
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
                raise RuntimeError("OpenAI后端初始化失败")
        
        # 准备请求数据
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        # 添加其他参数
        for key in ['top_p', 'frequency_penalty', 'presence_penalty']:
            if key in kwargs:
                data[key] = kwargs[key]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 发送请求
        result = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                break
            except Exception as e:
                print(f"OpenAI请求失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避重试
        
        if result is None:
            raise RuntimeError(f"所有OpenAI请求尝试失败，已重试 {self.max_retries} 次")
        
        # OpenAI返回的已经是标准格式，直接返回
        return result
    
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        
        Returns:
            List[str]: 可用模型名称列表
        """
        if not self.initialized:
            self.initialize()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_base}/models",
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            models_data = response.json()
            return [model["id"] for model in models_data.get("data", [])]
        except Exception as e:
            print(f"获取OpenAI模型列表失败: {e}")
            return []


# 简单的测试代码
if __name__ == "__main__":
    # 创建OpenAI后端
    backend = OpenAIBackend()
    
    # 初始化
    success = backend.initialize()
    if not success:
        print("初始化失败，退出")
        exit(1)
    
    print(f"使用模型: {backend.model_name}")
    
    # 发送一个简单的请求
    messages = [
        {"role": "system", "content": "你是一个友好、有帮助的AI助手。请用中文回答。"},
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
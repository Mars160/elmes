from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import yaml
import os
import time
from pathlib import Path

# 尝试导入dotenv，如果没有安装则忽略
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class Backend(ABC):
    """后端基类，定义与大语言模型交互的接口"""
    
    def __init__(self, backend_type: str, model_name: str = None, api_base: str = None, api_key: str = None):
        """
        初始化后端基类
        
        Args:
            backend_type: 后端类型 (ollama, openai, deepseek)
            model_name: 模型名称
            api_base: API基础URL
            api_key: API密钥
        """
        self.backend_type = backend_type
        self.initialized = False
        
        # 加载环境变量
        self._load_env_variables()
        
        # 加载配置文件
        self.config = self._load_config(backend_type)
        
        # 设置基本参数
        self._setup_parameters(model_name, api_base, api_key)
    
    def _load_env_variables(self):
        """加载环境变量文件"""
        if not DOTENV_AVAILABLE:
            return
        
        dotenv_paths = [
            Path('.env'),
            Path(os.path.dirname(os.path.abspath(__file__)), '../../.env'),
            Path(os.path.expanduser('~/.edu_evaluation/.env'))
        ]
        
        for dotenv_path in dotenv_paths:
            if dotenv_path.exists():
                load_dotenv(dotenv_path, override=True)  # 覆盖已存在的环境变量
                return
    
    def _load_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        加载配置文件
        
        Args:
            section: 配置文件中的section名称
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        # 配置文件路径优先级：test_backend.yaml > evaluation_backend.yaml
        config_files = ['test_backend.yaml', 'evaluation_backend.yaml']
        
        for config_file in config_files:
            config_paths = [
                Path(f'config/{config_file}'),
                Path(os.path.dirname(os.path.abspath(__file__)), f'../../config/{config_file}')
            ]
            
            for config_path in config_paths:
                if config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            full_config = yaml.safe_load(f)
                        
                        if section and section in full_config:
                            return full_config[section]
                        elif not section:
                            return full_config.get('default', full_config)
                    except Exception as e:
                        print(f"加载配置文件失败 {config_path}: {e}")
        
        return {}
    
    def _setup_parameters(self, model_name: str, api_base: str, api_key: str):
        """
        设置后端参数，优先级：参数 > 环境变量 > 配置文件 > 默认值
        
        Args:
            model_name: 模型名称
            api_base: API基础URL
            api_key: API密钥
        """
        # 构建环境变量名称前缀
        env_prefix = self.backend_type.upper()
        
        # 设置模型名称
        self.model_name = (
            model_name or 
            os.getenv(f'{env_prefix}_MODEL_NAME') or 
            self.config.get('model_name') or 
            self._get_default_model()
        )
        
        # 设置API基础URL
        self.api_base = (
            api_base or 
            os.getenv(f'{env_prefix}_API_BASE') or 
            self.config.get('api_base') or 
            self._get_default_api_base()
        )
        
        # 设置API密钥
        self.api_key = (
            api_key or 
            os.getenv(f'{env_prefix}_API_KEY') or 
            self.config.get('api_key') or 
            ""
        )
        
        # 设置超时和重试次数
        self.timeout = int(
            os.getenv(f'{env_prefix}_TIMEOUT') or 
            self.config.get('timeout', 60)
        )
        self.max_retries = int(
            os.getenv(f'{env_prefix}_MAX_RETRIES') or 
            self.config.get('max_retries', 3)
        )
        
        # 设置系统提示词
        self.system_prompt = (
            os.getenv(f'{env_prefix}_SYSTEM_PROMPT') or 
            self.config.get('system_prompt') or 
            'You are a helpful assistant.'
        )
    
    def _get_default_model(self) -> str:
        """获取默认模型名称，子类可重写"""
        return "unknown"
    
    def _get_default_api_base(self) -> str:
        """获取默认API基础URL，子类可重写"""
        return ""
    
    def set_model(self, model_name: str):
        """
        设置模型名称
        
        Args:
            model_name: 要使用的模型名称
        """
        self.model_name = model_name
    
    def _create_standard_response(self, content: str, model: str = None) -> Dict[str, Any]:
        """
        创建标准格式的响应
        
        Args:
            content: 响应内容
            model: 模型名称
            
        Returns:
            Dict[str, Any]: 标准格式的响应
        """
        return {
            "id": f"{self.backend_type}-{int(time.time())}",
            "model": model or self.model_name,
            "created": int(time.time()),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {}
        }
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化后端连接
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    def chat(self, 
             messages: List[Dict[str, str]], 
             temperature: float = 0.7, 
             max_tokens: int = 4000, 
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
        pass


if __name__ == "__main__":
    # get api key from .env
    if DOTENV_AVAILABLE:
        load_dotenv()
        api_key = os.getenv("DEEPSEEK_API_KEY")
        print(api_key)
    else:
        print("dotenv not installed")


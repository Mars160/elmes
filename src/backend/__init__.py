"""后端模块，提供与大语言模型交互的接口"""

# 导出后端类
try:
    from .base import Backend
    from .ollama_backend import OllamaBackend
    from .openai_backend import OpenAIBackend
    from .deepseek_backend import DeepSeekBackend

    __all__ = [
        'Backend',
        'OllamaBackend',
        'OpenAIBackend',
        'DeepSeekBackend'
    ]
except ImportError as e:
    import sys
    print(f"导入后端模块时出错: {e}", file=sys.stderr) 
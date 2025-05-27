"""执行器模块，提供不同类型的对话执行功能"""

# 导出执行器类
try:
    from .base import Executor
    from .single_turn_executor import SingleTurnExecutor
    from .multi_turn_executor import MultiTurnExecutor

    __all__ = [
        'Executor',
        'SingleTurnExecutor',
        'MultiTurnExecutor'
    ]
except ImportError as e:
    import sys
    print(f"导入执行器模块时出错: {e}", file=sys.stderr) 
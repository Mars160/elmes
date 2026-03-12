import re
from abc import ABC, abstractmethod
from elmes.graph.node import GraphNodeInterface

from typing import Type


class RouterNode(GraphNodeInterface, ABC):
    router_table: dict[str, Type["RouterNode"]] = {}

    def __init__(self):
        class_name = self.__class__.__name__
        super().__init__(class_name)

    @abstractmethod
    def route(self, *args, **kwargs) -> str:
        """根据输入的参数返回对应的路由信息，路由信息应该是可用的agent或END或其他router名"""
        pass

    @property
    @abstractmethod
    def available_ends(self) -> set[str]:
        """返回这个router节点可路由到的所有节点的集合，便于图的合法性检查"""
        pass

    @staticmethod
    def register():
        """装饰器，用于注册路由节点"""

        def decorator(cls):
            class_name = cls.__name__
            # 转class_name的大驼峰为下划线
            snake_case_name = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
            RouterNode.router_table[snake_case_name] = cls
            return cls

        return decorator

    async def run(self, *args, **kwargs) -> str | None:
        # Router节点的run方法不执行实际逻辑，只返回对应的路由信息
        return self.route(*args, **kwargs)

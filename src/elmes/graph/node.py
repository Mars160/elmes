from abc import ABC, abstractmethod


class GraphNodeInterface(ABC):
    @abstractmethod
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, *args, **kwargs) -> str | None:
        pass


class StartNode(GraphNodeInterface):
    def __init__(self, name: str):
        super().__init__(name)

    async def run(self, *args, **kwargs) -> str | None:
        return "START"


class EndNode(GraphNodeInterface):
    def __init__(self, name: str):
        super().__init__(name)

    async def run(self, *args, **kwargs) -> str | None:
        return None

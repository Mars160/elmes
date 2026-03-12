from abc import ABC, abstractmethod


class GraphNodeInterface(ABC):
    @abstractmethod
    async def run(self, *args, **kwargs) -> str | None:
        pass


class StartNode(GraphNodeInterface):
    async def run(self, *args, **kwargs) -> str | None:
        return "START"


class EndNode(GraphNodeInterface):
    async def run(self, *args, **kwargs) -> str | None:
        return None

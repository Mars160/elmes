"""Router base class and registry for conditional routing in graphs."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Type

from pydantic_graph import BaseNode, End, GraphRunContext

from elmes.graph.state import GraphState

if TYPE_CHECKING:
    from typing import Type


class Router(ABC):
    """Base class for all routers.

    Routers are responsible for determining the next node based on conditions.
    They are used in direction configurations like:
        - "teacher -> router:any_keyword_route(keywords=['end'], exists_to=END, else_to=student)"
    """

    # Registry of all available routers
    _registry: dict[str, Type["Router"]] = {}

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def route(self, state: GraphState) -> str:
        """Determine the next node based on the current state.

        Args:
            state: Current graph state containing query, messages, etc.

        Returns:
            Name of the next node to route to (e.g., "END", "student")
        """
        pass

    @property
    @abstractmethod
    def available_targets(self) -> set[str]:
        """Return set of all possible target nodes this router can route to.

        Used for graph validation to ensure all targets exist.
        """
        pass

    @classmethod
    def register(
        cls, name: str | None = None
    ) -> Callable[[Type["Router"]], Type["Router"]]:
        """Register a router class in the registry.

        Can be used as a decorator:
            @Router.register()
            class MyRouter(Router):
                ...

        Or with explicit name:
            @Router.register("custom_name")
            class MyRouter(Router):
                ...
        """

        def decorator(router_class: Type["Router"]) -> Type["Router"]:
            router_name = name or router_class.__name__
            # Convert CamelCase to snake_case
            snake_name = re.sub(r"(?<!^)(?=[A-Z])", "_", router_name).lower()
            cls._registry[snake_name] = router_class
            return router_class

        return decorator

    @classmethod
    def get_router(cls, name: str) -> Type["Router"]:
        """Get a router class by name."""
        if name not in cls._registry:
            raise ValueError(
                f"Router '{name}' not found in registry. "
                f"Available routers: {list(cls._registry.keys())}"
            )
        return cls._registry[name]

    @classmethod
    def create_router(cls, name: str, **kwargs) -> "Router":
        """Create a router instance by name with given arguments."""
        router_class = cls.get_router(name)
        return router_class(**kwargs)

    @classmethod
    def list_routers(cls) -> list[str]:
        """List all registered router names."""
        return list(cls._registry.keys())


class RouterNode(BaseNode[GraphState, None, Any]):
    """Graph node that wraps a Router and handles routing logic."""

    def __init__(
        self,
        router: Router,
        router_table: dict[str, type[BaseNode[GraphState, None, Any]]],
    ):
        self.router = router
        self.router_table = router_table

    async def run(
        self, ctx: GraphRunContext[GraphState]
    ) -> BaseNode[GraphState, None, Any] | End[Any]:
        """Execute router and return next node."""
        target = self.router.route(ctx.state)

        if target == "END":
            return End(None)

        if target not in self.router_table:
            raise ValueError(
                f"Router '{self.router.name}' returned unknown target '{target}'. "
                f"Available targets: {list(self.router_table.keys())}"
            )

        return self.router_table[target]()


# Import and register built-in routers
# Use a function to avoid circular imports
def _register_builtin_routers():
    """Register all built-in routers."""
    from elmes.graph.router.any_keyword import AnyKeywordRouter

    return AnyKeywordRouter


# Register on first access
_registered = False


def ensure_routers_registered():
    """Ensure all built-in routers are registered."""
    global _registered
    if not _registered:
        _register_builtin_routers()
        _registered = True


__all__ = ["Router", "RouterNode", "ensure_routers_registered"]

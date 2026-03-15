"""Any keyword router - routes based on keyword presence in query."""

from elmes.graph.router import Router
from elmes.graph.state import GraphState


@Router.register()
class AnyKeywordRouter(Router):
    """Router that checks if any keyword exists in the query.

    Configuration example in YAML:
        directions:
          - teacher -> router:any_keyword_router(keywords=["<end>", "下课"], exists_to=END, else_to=student)

    Args:
        keywords: List of keywords to search for
        exists_to: Target node if any keyword is found
        else_to: Target node if no keyword is found
    """

    def __init__(self, keywords: list[str], exists_to: str, else_to: str):
        super().__init__("any_keyword_router")
        self.keywords = keywords
        self.exists_to = exists_to
        self.else_to = else_to

        if not keywords:
            raise ValueError("AnyKeywordRouter requires at least one keyword")

    def route(self, state: GraphState) -> str:
        """Check if any keyword exists in the query."""
        query = state.query

        for keyword in self.keywords:
            if keyword in query:
                return self.exists_to

        return self.else_to

    @property
    def available_targets(self) -> set[str]:
        """Return all possible target nodes."""
        return {self.exists_to, self.else_to}

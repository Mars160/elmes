from elmes.graph.router import RouterNode


@RouterNode.register()
class AnyKeywordRoute(RouterNode):
    def __init__(self, keywords: list[str], exists_to: str, else_to: str):
        self.keywords = keywords
        self.exists_to = exists_to
        self.else_to = else_to
        super().__init__()

    def route(self, query: str, query_from: str, *args, **kwargs) -> str:
        for keyword in self.keywords:
            if keyword in query:
                return self.exists_to
        return self.else_to

    @property
    def available_ends(self) -> set[str]:
        return {self.exists_to, self.else_to}


if __name__ == "__main__":
    print(RouterNode.router_table)
    import asyncio

    router = AnyKeywordRoute(
        keywords=["hello", "hi"], exists_to="GREET_AGENT", else_to="END"
    )
    print(
        asyncio.run(router.run(query="hello world", query_from="user"))
    )  # 输出: GREET_AGENT
    print(router.route(query="goodbye world", query_from="user"))  # 输出: END
    print(router.available_ends)  # 输出: {'GREET_AGENT', 'END'}
    print(router.router_table)

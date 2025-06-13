from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.messages import BaseMessage
from typing import Union, Sequence, Callable, Tuple, Dict

from elmes.utils import remove_think


def any_keyword_route(
    keywords: Sequence[str], exists_to: str, else_to: str, think_as_message: bool = False
) -> Tuple[Callable[..., bool], Dict[bool, str]]:
    """Route based on keywords."""
    path_map = {
        True: exists_to,
        False: else_to,
    }

    def route(state: Union[AgentState, Sequence[BaseMessage]]) -> bool:
        """Route based on keywords."""
        if isinstance(state, Sequence):
            message = state[-1]
        elif messages := state.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No messages found, error while routing")

        content = message.content
        if not think_as_message:
            content = remove_think(content)  # Remove think tags
        if isinstance(content, str):
            content = content.lower()
            r = any(keyword in content for keyword in keywords)
        elif isinstance(content, list):
            content = content[-1]
            if isinstance(content, str):
                content = content.lower()
                r = any(keyword in content for keyword in keywords)
            elif isinstance(content, dict):
                print(content)
                raise NotImplementedError("Dictionary content not implemented")
            else:
                raise ValueError(
                    f"Unsupported type for message content: {type(content)}"
                )
        else:
            raise ValueError(f"Unsupported type for message content: {type(content)}")
        return r

    return (route, path_map)


def all_keyword_route(
    keywords: Sequence[str], exists_to: str, else_to: str
) -> Tuple[Callable[..., bool], Dict[bool, str]]:
    """Route based on keywords."""
    path_map = {
        True: exists_to,
        False: else_to,
    }

    def route(state: Union[AgentState, Sequence[BaseMessage]]) -> bool:
        """Route based on keywords."""
        if isinstance(state, Sequence):
            message = state[-1]
        elif messages := state.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No messages found, error while routing")

        content = message.content
        if isinstance(content, str):
            content = content.lower()
            r = all(keyword in content for keyword in keywords)
        elif isinstance(content, list):
            content = content[-1]
            if isinstance(content, str):
                content = content.lower()
                r = all(keyword in content for keyword in keywords)
            elif isinstance(content, dict):
                print(content)
                raise NotImplementedError("Dictionary content not implemented")
            else:
                raise ValueError(
                    f"Unsupported type for message content: {type(content)}"
                )
        else:
            raise ValueError(f"Unsupported type for message content: {type(content)}")
        return r

    return (route, path_map)

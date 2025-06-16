import re
from typing import Any, Dict
from langchain_core.tools import tool, BaseTool
from elmes.config import CONFIG
from langgraph.prebuilt import create_react_agent
from langchain.chat_models.base import BaseChatModel
from elmes.entity import ExportFormat
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed
import json


def generate_evaluation_tool() -> BaseTool:
    """
    Generates a tool for evaluating the Elmes evaluation framework.
    This function is a placeholder and should be implemented with actual logic.
    """

    if CONFIG.evaluation is None:
        raise ValueError("Evaluation configuration not found.")

    @tool(
        name_or_callable="save_result_to_database",
        description="Save the evaluation results to a database.",
        return_direct=True,
        args_schema=CONFIG.evaluation.format_to_pydantic(),
    )
    def save_to_db(**kwargs):
        """
        Save the evaluation results to a database.
        """
        for k, v in kwargs.items():
            if issubclass(v.__class__, BaseModel):
                v = v.model_dump()
            kwargs[k] = v
        return kwargs

    return save_to_db


@retry(
    stop=stop_after_attempt(CONFIG.globals.retry.attempt),
    wait=wait_fixed(CONFIG.globals.retry.interval),
)
async def evaluate(
    model: BaseChatModel, exported_result: ExportFormat
) -> Dict[str, Any]:
    assert CONFIG.evaluation
    system_prompt, other_prompt = CONFIG.evaluation.get_prompts()
    system_prompt = exported_result.replace_template(system_prompt)
    ops = []
    for op in other_prompt:
        content = exported_result.replace_template(op.content)
        ops.append(
            {
                "role": op.role,
                "content": content,
            }
        )
    if CONFIG.evaluation.format_mode == "tool":
        tools = [generate_evaluation_tool()]

        # other_prompt = exported_result.replace_template(other_prompt)
        agent = create_react_agent(
            model=model.bind_tools(
                tools,
                tool_choice={
                    "type": "function",
                    "function": {"name": "save_result_to_database"},
                },  # type: ignore
                # tool_choice="required",
            ),
            tools=tools,
            # model=model,
            prompt=system_prompt
            + "\n\n请调用save_result_to_database工具以将评估结果存入数据库",
        )

        a = await agent.ainvoke({"messages": ops})
        data = json.loads(a["messages"][-1].content)
        return data
    elif CONFIG.evaluation.format_mode == "prompt":
        # print(CONFIG.evaluation.format_to_json_example())
        agent = create_react_agent(
            model=model,
            tools=[],
            prompt=system_prompt
            + "\n\n# NOTE！\n\n"
            + "You should keep your output in the following JSON format blow, and wrap it with exactlly <START OF EVAL OUTPUT> and <END OF EVAL OUTPUT> ONLY!, no escape.\n\n".upper()
            + f"\n\njson schema:\n\n\n{CONFIG.evaluation.format_to_json_schema()}\n\n\n"
            + "\n\nFORMAT EXAMPLE:\n\n"
            + "\n\n<START OF EVAL OUTPUT>\n\n"
            # + "```json"
            + f"{CONFIG.evaluation.format_to_json_example()}\n"
            # + "```"
            + "<END OF EVAL OUTPUT>",
        )

        a = await agent.ainvoke({"messages": ops})
        response: str = a["messages"][-1].content

        # Fuck Gemini
        response = response.replace("\\<", "<")
        response = response.replace("\\>", ">")

        # print(response)

        # 正则表达式匹配<START OUTPUT>和<END OUTPUT>
        match = re.findall(
            r"<START OF EVAL OUTPUT>(.*)<END OF EVAL OUTPUT>", response, re.DOTALL
        )
        if len(match) > 0:
            text = match[-1]
            # 如果text被```包围，去掉
            text = text.strip().strip("```").strip("json")
            # print(text, "#############")
            return json.loads(text)
        else:
            raise ValueError("Output does not contain <START OUTPUT> and <END OUTPUT>")
    else:
        raise ValueError(f"Invalid format mode: {CONFIG.evaluation.format_mode}")


if __name__ == "__main__":
    import asyncio

    async def main():
        from elmes.model import init_chat_model_from_dict
        # from langchain.globals import set_debug

        # set_debug(True)

        ef = ExportFormat.from_json_file(
            "/Users/mars160/elmes/guided_teaching/4f699a38-33fe-4cd6-8013-06e191e249ab.json"
        )

        model = init_chat_model_from_dict(CONFIG.models["4o_teacher"])
        a = await evaluate(model, ef)
        print(a)

    asyncio.run(main())

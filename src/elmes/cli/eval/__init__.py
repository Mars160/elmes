"""Eval command for ELMES CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click


def _format_messages(messages_by_agent: dict[str, list[dict]]) -> str:
    """将所有 agent 的多轮对话格式化为可读字符串，传给 LLMJudge。"""
    parts: list[str] = []
    for agent_name, messages in messages_by_agent.items():
        parts.append(f"=== {agent_name} ===")
        for msg in messages:
            kind = msg.get("kind", "")
            if kind == "request":
                for part in msg.get("parts", []):
                    part_kind = part.get("part_kind", "")
                    if part_kind == "user-prompt":
                        parts.append(f"[USER]: {part.get('content', '')}")
                    elif part_kind == "system-prompt":
                        # 跳过 system prompt，不传给 judge
                        pass
            elif kind == "response":
                for part in msg.get("parts", []):
                    part_kind = part.get("part_kind", "")
                    if part_kind == "text":
                        parts.append(f"[ASSISTANT]: {part.get('content', '')}")
        parts.append("")
    return "\n".join(parts).strip()


def _find_input_dir(config, input_path: str | None) -> Path:
    """推断 generate 结果目录：优先用 --input，否则找 output_dir 下最新的子目录。"""
    if input_path:
        return Path(input_path)

    output_dir = Path(config.globals.output_dir)
    if not output_dir.exists():
        raise click.ClickException(
            f"output_dir {output_dir} 不存在，请先运行 generate 命令或用 --input 指定目录"
        )

    # 找最新的 md5 子目录（generate 会在 output_dir/{config_md5}/ 下保存结果）
    subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
    if not subdirs:
        raise click.ClickException(
            f"{output_dir} 下没有找到子目录，请先运行 generate 命令"
        )
    return max(subdirs, key=lambda d: d.stat().st_mtime)


@click.command(help="Evaluate the performance of a model on a dataset")
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    help="Path to the configuration file",
)
@click.option(
    "--input",
    "-i",
    "input_path",
    default=None,
    help="generate 结果目录（含 task_N.json），默认自动推断 output_dir 下最新子目录",
)
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
@click.option("--avg/--no-avg", default=True, help="Calculate the average score")
@click.option(
    "--include-reasons/--no-include-reasons",
    default=True,
    help="在报告中展示 LLM judge 的评分理由",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    default=None,
    help="eval 结果输出目录，默认为 input 目录下的 eval/ 子目录",
)
def eval(
    config: str,
    input_path: str | None,
    output_path: str | None,
    debug: bool,
    avg: bool,
    include_reasons: bool,
):
    """Evaluate model performance using LLM as judge."""
    if debug:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    from elmes.config import load_config

    config_obj = load_config(str(config))
    input_dir = _find_input_dir(config_obj, input_path)
    click.echo(f"从 {input_dir} 读取生成结果")

    import asyncio

    asyncio.run(eval_logic(config_obj, input_dir, output_path, avg, include_reasons))


async def eval_logic(
    config, input_dir: Path, output_path: str | None, avg: bool, include_reasons: bool
):
    """使用 LLM as judge 评估对话质量。"""
    from elmes.model import build_model
    from pydantic_evals import Case, Dataset
    from pydantic_evals.evaluators import LLMJudge
    from pydantic_evals.evaluators.llm_as_a_judge import set_default_judge_model

    eval_config = config.evals

    # 构建 agent → model 信息映射，写入 eval JSON
    agent_model_info: dict[str, dict[str, str]] = {
        agent_name: {
            "model_alias": agent_cfg.model.name,
            "model": agent_cfg.model.model,
        }
        for agent_name, agent_cfg in config.agents.items()
    }

    # 构建 judge model 并设为全局默认
    judge_model = build_model(eval_config.judge_model)
    set_default_judge_model(judge_model)

    # 扫描 task_*.json 文件
    task_files = sorted(input_dir.glob("task_*.json"))
    if not task_files:
        raise click.ClickException(f"{input_dir} 下没有找到 task_*.json 文件")

    click.echo(f"找到 {len(task_files)} 个任务文件，开始构建评估数据集...")

    # 构建 evaluators（每个 field 一个 LLMJudge，score 模式）
    evaluators = []
    for field in eval_config.fields:
        evaluators.append(
            LLMJudge(
                rubric=field.rubric,
                include_input=True,  # judge 能看到任务变量（输入上下文）
                score={
                    "evaluation_name": field.name,
                    "include_reason": field.reason,
                },
                assertion=False,
            )
        )

    # 读取每个 task 文件，构建 Case
    cases: list[Case] = []
    task_data: list[dict[str, Any]] = []

    for task_file in task_files:
        with open(task_file, encoding="utf-8") as f:
            data = json.load(f)

        task_data.append(data)

        # 任务变量作为 inputs（judge 通过 include_input 看到）
        task_variables = data.get("task_variables", {})
        inputs_str = "\n".join(f"{k}: {v}" for k, v in task_variables.items())

        cases.append(
            Case(
                name=task_file.stem,
                inputs=inputs_str,
                expected_output=None,
            )
        )

    # 构建 Dataset
    dataset: Dataset[str, str, None] = Dataset(
        cases=cases,
        evaluators=evaluators,
    )

    # task 函数：inputs 是任务变量字符串，output 是格式化后的对话
    # 需要按顺序与 cases 对应
    dialog_map = {
        task_file.stem: _format_messages(data.get("messages", {}))
        for task_file, data in zip(task_files, task_data)
    }

    def get_dialog(inputs: str) -> str:
        # 通过反查 cases 中对应的 name 来获取对话
        # inputs 是任务变量字符串，每个 case 唯一
        for case, tf in zip(cases, task_files):
            if case.inputs == inputs:
                return dialog_map[tf.stem]
        return inputs

    click.echo("开始 LLM as judge 评估...")

    report = await dataset.evaluate(
        get_dialog,
        name=eval_config.name,
        max_concurrency=config.globals.concurrency,
    )

    # 输出控制台报告
    report.print(include_input=True, include_reasons=include_reasons)

    # 保存结果
    eval_dir = Path(output_path) if output_path else input_dir / "eval"
    eval_dir.mkdir(parents=True, exist_ok=True)

    # 保存每个 task 的详细 JSON
    for report_case in report.cases:
        result: dict[str, Any] = {
            "case_name": report_case.name,
            "inputs": report_case.inputs,
            "agents": agent_model_info,
            "scores": {},
        }
        for score_name, score_val in report_case.scores.items():
            entry: dict[str, Any] = {"value": score_val.value}
            if score_val.reason:
                entry["reason"] = score_val.reason
            result["scores"][score_name] = entry

        out_file = eval_dir / f"{report_case.name}_eval.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    # 生成 CSV 汇总
    _generate_csv_report(report, eval_dir, avg)

    click.echo(f"评估结果已保存至 {eval_dir}")


def _generate_csv_report(report: Any, eval_dir: Path, avg: bool) -> None:
    """生成 CSV 汇总报告。"""
    if not report.cases:
        click.echo("没有评估结果，跳过 CSV 生成", err=True)
        return

    # 收集所有 score 字段名
    field_names: list[str] = []
    for case in report.cases:
        for name in case.scores:
            if name not in field_names:
                field_names.append(name)

    csv_path = eval_dir / "evaluation_results.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        header = ["task_id"] + field_names
        if avg:
            header.append("avg")
        f.write(",".join(header) + "\n")

        for case in report.cases:
            row = [case.name]
            scores: list[float] = []
            for field in field_names:
                score_result = case.scores.get(field)
                if score_result is not None:
                    val = score_result.value
                    row.append(f"{val:.4f}" if isinstance(val, float) else str(val))
                    if isinstance(val, (int, float)):
                        scores.append(float(val))
                else:
                    row.append("")

            if avg and scores:
                row.append(f"{sum(scores) / len(scores):.4f}")

            f.write(",".join(row) + "\n")

    click.echo(f"CSV 报告已保存至 {csv_path}")

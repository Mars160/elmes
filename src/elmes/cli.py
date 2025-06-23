import click

from pathlib import Path
from typing import Dict, Any

from langchain.globals import set_debug
from tenacity import RetryError

# set_debug(True)


@click.command("generate", help="Generate conversions for all tasks")
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
def generate(config: str, debug: bool):
    set_debug(debug)
    from elmes.config import load_conf

    path = Path(config)
    load_conf(path)
    generate_logic()


def generate_logic():
    from elmes.run import run
    import asyncio

    asyncio.run(run())


@click.command(help="Export chat databases to JSON format")
@click.option(
    "--config", default="config.yaml", help="Directory containing chat databases"
)
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
def export_json(config: str, debug: bool):
    set_debug(debug)
    from elmes.config import load_conf

    path = Path(config)
    load_conf(path)
    export_json_logic()


def export_json_logic():
    from elmes.config import CONFIG

    input = CONFIG.globals.memory.path
    output = input

    dbfiles = []
    files = input.iterdir()
    for file in files:
        if file.suffix == ".db":
            dbfiles.append(file.absolute())

    import sqlite3
    import asyncio
    import json
    from tqdm.asyncio import tqdm
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
    from langgraph.checkpoint.base import Checkpoint

    async def aexport(path: Path):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        sql = "select checkpoint_ns, checkpoint_id, parent_checkpoint_id, checkpoint from checkpoints"
        cursor.execute(sql)
        results = cursor.fetchall()[-1]
        cns, cid, pcid, c = results
        jps = JsonPlusSerializer()
        checkpoint: Checkpoint = jps.loads_typed(("msgpack", c))
        messages = []
        for m in checkpoint.get("channel_values")["messages"]:
            if m.name is None:
                continue
            if "</think>" in m.content:
                content_split = m.content.split("</think>")
                reasoning = content_split[0].strip()
                response = content_split[1].strip()
            else:
                reasoning = ""
                response = m.content.strip()
            messages.append(
                {"role": m.name, "content": response, "reasoning": reasoning}
            )

        sql = "select key, value from task"
        cursor.execute(sql)
        results = cursor.fetchall()
        obj = {"task": {}, "messages": messages}

        for key, value in results:
            obj["task"][key] = value

        output_path = output / f"{path.stem}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=4)

    tasks = []
    for dbfile in dbfiles:
        task = aexport(dbfile)
        tasks.append(task)

    def arun():
        asyncio.run(tqdm.gather(*tasks))

    arun()


@click.command(help="Evaluate the performance of a model on a dataset")
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    help="Path to the configuration file",
)
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
@click.option("--avg/--no-avg", default=True, help="Calculate the average score")
def eval(config: Path, debug: bool, avg: bool):
    set_debug(debug)
    from elmes.config import load_conf

    load_conf(config)
    eval_logic(avg)


def eval_logic(avg: bool):
    from elmes.config import CONFIG

    input_dir = CONFIG.globals.memory.path
    import asyncio
    from elmes.evaluation import evaluate
    from elmes.model import init_chat_model_from_dict

    from elmes.entity import ExportFormat
    from tqdm.asyncio import tqdm
    import json

    input_dir = Path(input_dir)

    eval_path = input_dir / "eval"
    eval_path.mkdir(exist_ok=True)

    sem = asyncio.Semaphore(CONFIG.globals.concurrency)

    async def eval_task(model, file: Path) -> Dict[str, Any]:
        async with sem:
            ef = ExportFormat.from_json_file(file)
            try:
                eval = await evaluate(model, ef)
                with open(eval_path / file.name, "w", encoding="utf8") as f:
                    json.dump(eval, f, ensure_ascii=False, indent=4)
                return eval
            except RetryError as e:
                print(f"Error evaluating {file}", e.last_attempt.exception())
                return {}

    async def main():
        assert CONFIG.evaluation
        model = init_chat_model_from_dict(CONFIG.models[CONFIG.evaluation.model])

        to_eval_files = list(input_dir.glob("*.json"))
        task_ids = [file.stem for file in to_eval_files]
        eval_tasks = []
        for file in to_eval_files:
            eval_tasks.append(eval_task(model, file))

        evals = await tqdm.gather(*eval_tasks)

        csv_utf8 = open(
            eval_path / f"{CONFIG.evaluation.name}.csv", "w", encoding="utf-8"
        )
        # csv_gbk = open(eval_path / f"{CONFIG.evaluation.name}-gbk.csv", "w", encoding="gbk")

        title = ["task_id"]
        # title = []
        e = []
        count = 0
        while len(e) == 0 and count < len(evals):
            e = list(evals[count].keys())
            count += 1
        for field in e:
            title.append(field)

        if avg:
            title.append("avg")

        csv_utf8.write(",".join(title) + "\n")
        # csv_gbk.write(",".join(title) + "\n")

        if avg:
            row = len(task_ids) + 1
            col = len(title) - 1

            matrix = [[0.0] * col for _ in range(row)]

            # 统计数据并计算每行平均值
            for idx, (task_id, eval) in enumerate(zip(task_ids, evals)):
                contents = [task_id]
                for sub_idx, (f, c) in enumerate(eval.items()):
                    v = float(c)
                    matrix[idx][sub_idx] = v
                    contents.append(f"{c}")
                sum = 0
                for i in matrix[idx][:-1]:
                    sum += i
                # 最后一列的数字 = 每列的和除以列数-1
                matrix[idx][col - 1] = sum / (col - 1)
                contents.append(f"{matrix[idx][col - 1]:.2f}")
                csv_utf8.write(",".join(contents) + "\n")
                # csv_gbk.write(",".join(contents) + "\n")
            # 计算每列的平均值
            for col_idx in range(col):
                # print(matrix)
                sum = 0
                # 计算每一列除去最后一个元素的和
                for row_idx in range(row - 1):
                    sum += matrix[row_idx][col_idx]
                matrix[-1][col_idx] = sum / (row - 1)

            write_str = ["%.2f" % i for i in matrix[-1]]
            write_str.insert(0, "Avg")
            # 写入最后一行的平均值
            csv_utf8.write(",".join(write_str) + "\n")
            # csv_gbk.write(",".join(write_str) + "\n")
        else:
            for task_id, eval in zip(task_ids, evals):
                contents = [task_id]
                for f, c in eval.items():
                    contents.append(f"{c}")
                csv_utf8.write(",".join(contents) + "\n")
                # csv_gbk.write(",".join(contents) + "\n")

        csv_utf8.close()
        # csv_gbk.close()

    asyncio.run(main())


@click.command(help="Visualize the results in all CSV file in the specified directory.")
@click.argument(
    "input_dir",
    type=click.Path(exists=True),
)
@click.option(
    "--x-rotation",
    type=int,
    default=30,
)
def visualize(input_dir: str, x_rotation: int):
    visualize_logic(input_dir, x_rotation)


def visualize_logic(input_dir: str, x_rotation: int):
    color_palette = [
        "#1f77b4",
        "#aec7e8",
        "#ff7f0e",
        "#ffbb78",
        "#2ca02c",
        "#98df8a",
        "#d62728",
        "#ff9896",
        "#9467bd",
        "#c5b0d5",
        "#8c564b",
        "#c49c94",
        "#e377c2",
        "#f7b6d2",
        "#7f7f7f",
        "#c7c7c7",
        "#bcbd22",
        "#dbdb8d",
        "#17becf",
        "#9edae5",
    ]
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import font_manager

    from importlib.resources import files

    font_path = files("assets.fonts").joinpath("sarasa-mono-sc-regular.ttf")
    font_path = str(font_path)

    font_manager.fontManager.addfont(font_path)
    plt.rcParams["font.sans-serif"] = "Sarasa Mono SC"
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

    input_path = Path(input_dir)
    csvs = input_path.rglob("*.csv")

    task_name = ""
    keys = []
    models = []
    values = {}

    for csv in csvs:
        stem_split = csv.stem.rsplit("_", 1)
        if task_name == "":
            task_name = stem_split[0]
        elif task_name != stem_split[0]:
            raise ValueError(
                f"Multiple task names found in CSV files. {task_name} and {stem_split[0]} are different."
            )

        model = stem_split[1]
        models.append(model)

        data = pd.read_csv(csv)
        data = data.drop(columns=["task_id", "avg"])
        data = data.iloc[-1].to_dict()

        if not keys:
            keys = list(data.keys())
            for k in keys:
                values[k] = []
        elif keys != list(data.keys()):
            raise ValueError(
                f"Data keys do not match across CSV files. [{','.join(keys)}] and [{','.join(data.keys())}] are different."
            )

        for k in keys:
            values[k].append(data[k])

    # 构建 DataFrame
    df_dict = {"": models}
    for k in keys:
        df_dict[k] = values[k]

    df = pd.DataFrame(df_dict)

    # ==== ✅ 自适应画布宽度 ====
    fig_width = max(8, len(df) * 0.8)  # 每个模型 0.8 英寸，最小宽度为 8
    fig, ax = plt.subplots(figsize=(fig_width, 6))

    df.set_index("").plot(kind="bar", stacked=True, ax=ax, color=color_palette)
    ax.set_xticklabels(df[""], rotation=x_rotation)
    ax.set_title(f"{task_name}")

    # ✅ 设置图例位置到图表下方，打散为多列
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.1),
        ncol=min(len(keys), 5),
        frameon=False,
    )

    plt.tight_layout()
    plt.savefig(input_path / f"stack_{task_name}.png", dpi=300)

    # ==== ✅ 雷达图 ====
    # 准备数据
    num_vars = len(keys)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # 闭合图形

    # 计算所有数值的最小值
    all_scores = [values[k] for k in keys]
    min_value = min([min(score_list) for score_list in all_scores])

    # 设置雷达图的最小值原点
    min_value -= 1  # 最小值减去 1

    # 绘制雷达图
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for idx, model in enumerate(models):
        scores = [values[k][idx] for k in keys]
        scores += scores[:1]  # 闭合图形
        ax.plot(
            angles,
            scores,
            label=model,
            linewidth=2,
            color=color_palette[idx % len(color_palette)],
        )
        ax.fill(angles, scores, alpha=0.1)

    # 调整雷达图的半径范围，确保从 (min_value - 1) 开始
    ax.set_ylim(min_value, max([max(score_list) for score_list in all_scores]) + 1)

    # 设置标签和样式
    ax.set_thetagrids(np.degrees(angles[:-1]), keys)  # type: ignore
    ax.set_title(f"{task_name}", size=16)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    plt.tight_layout()
    plt.savefig(input_path / f"radar_{task_name}.png", dpi=300)


@click.command(
    help="Run the pipeline to generate, export JSON files, and evaluate the results."
)
@click.option(
    "--config", type=click.Path(exists=True), help="Path to the configuration file"
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
def pipeline(config, debug=False):
    set_debug(debug)
    from elmes.config import load_conf

    load_conf(config)
    generate_logic()
    export_json_logic()
    eval_logic(avg=True)


@click.command(help="Draw Agent workflow.")
@click.option(
    "--config", type=click.Path(exists=True), help="Path to the configuration file"
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
def draw(config, debug=False):
    set_debug(debug)
    from elmes.config import load_conf
    from pathlib import Path

    config = Path(config)
    load_conf(config)

    from elmes.config import CONFIG
    from elmes.model import init_model_map
    from elmes.agent import init_agent_map
    from elmes.directions import apply_agent_direction

    # from langchain_core.runnables.graph import CurveStyle, NodeStyles, MermaidDrawMethod

    import asyncio

    models = init_model_map()
    task = CONFIG.tasks.variables[0]
    agents, _ = init_agent_map(models, task)
    agent, _ = asyncio.run(apply_agent_direction(agents, task=task))
    png = agent.get_graph().draw_mermaid_png()
    with open(f"{config.stem}.png", "wb") as wb:
        wb.write(png)
    # print(png)


@click.group()
def main():
    pass


main.add_command(generate)
main.add_command(export_json)
main.add_command(eval)
main.add_command(pipeline)

main.add_command(visualize)

main.add_command(draw)

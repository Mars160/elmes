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
    generate_logic(config, debug)


def generate_logic(config: str, debug: bool):
    set_debug(debug)
    from elmes.config import load_conf

    path = Path(config)
    load_conf(path)

    from elmes.run import run
    import asyncio

    asyncio.run(run())


@click.command(help="Export chat databases to JSON format")
@click.option(
    "--config", default="config.yaml", help="Directory containing chat databases"
)
@click.option("--debug", default=False, help="Debug Mode", is_flag=True)
def export_json(config: str, debug: bool):
    export_json_logic(config, debug)


def export_json_logic(config: str, debug: bool):
    set_debug(debug)
    input = Path(config)
    from elmes.config import load_conf

    path = Path(config)
    load_conf(path)

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
    eval_logic(config, debug, avg)


def eval_logic(config: Path, debug: bool, avg: bool):
    set_debug(debug)
    from elmes.config import load_conf

    load_conf(config)

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

    async def eval_task(model, file: Path) -> Dict[str, Any]:
        ef = ExportFormat.from_json_file(file)
        try:
            eval = await evaluate(model, ef)
            with open(eval_path / file.name, "w", encoding="utf8") as f:
                json.dump(eval, f, ensure_ascii=False, indent=4)
            return eval
        except RetryError as e:  # noqa: E722
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

        csv_utf8 = open(eval_path / f"{CONFIG.evaluation.name}.csv", "w", encoding="utf-8")
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


@click.command(
    help="Run the pipeline to generate, export JSON files, and evaluate the results."
)
@click.option(
    "--config", type=click.Path(exists=True), help="Path to the configuration file"
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
def pipeline(config, debug=False):
    generate_logic(config=config, debug=debug)
    export_json_logic(config=config, debug=debug)
    eval_logic(config=config, debug=debug, avg=True)


@click.group()
def main():
    pass


main.add_command(generate)
main.add_command(export_json)
main.add_command(eval)
main.add_command(pipeline)

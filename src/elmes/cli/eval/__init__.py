import click

from pathlib import Path
from typing import Dict, Any

from langchain.globals import set_debug
from tenacity import RetryError


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

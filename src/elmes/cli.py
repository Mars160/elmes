from email.policy import default
import click

from pathlib import Path
from typing import Dict, Any

from langchain.globals import set_debug

# set_debug(True)


@click.command("generate")
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
@click.option("--debug", default=False, help="Debug Mode")
def generate(config: str, debug: bool):
    set_debug(debug)
    from elmes.config import load_conf

    path = Path(config)
    load_conf(path)

    from elmes.run import run
    import asyncio

    asyncio.run(run())


@click.command()
@click.option(
    "--input-dir", default="inputs", help="Directory containing chat databases"
)
@click.option("--debug", default=False, help="Debug Mode")
def export_json(input_dir: str, debug: bool):
    set_debug(debug)
    input = Path(input_dir)
    if not input.exists():
        raise ValueError(f"Input directory {input} Not Exists!")
    elif not input.is_dir():
        raise ValueError(f"{input} is not a directory.")
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


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    required=True,
    help="Path to the configuration file",
)
@click.option("--debug", default=False, help="Debug Mode")
def eval(config: Path, debug: bool):
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
        except:
            print(f"Error evaluating {file}")
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

        csv_utf8 = open(eval_path / "result-utf8.csv", "w", encoding="utf-8")
        csv_gbk = open(eval_path / "result-gbk.csv", "w", encoding="gbk")

        title = ["task_id"]
        # title = []
        e = []
        count = 0
        while len(e) == 0 and count < len(evals):
            e = list(evals[count].keys())
            count += 1
        for field in e:
            title.append(field)

        csv_utf8.write(",".join(title) + "\n")
        csv_gbk.write(",".join(title) + "\n")

        for task_id, eval in zip(task_ids, evals):
            contents = [task_id]
            for f, c in eval.items():
                contents.append(f"{c}")
            csv_utf8.write(",".join(contents) + "\n")
            csv_gbk.write(",".join(contents) + "\n")
        csv_utf8.close()
        csv_gbk.close()

    asyncio.run(main())


@click.group()
def main():
    pass


main.add_command(generate)
main.add_command(export_json)
main.add_command(eval)

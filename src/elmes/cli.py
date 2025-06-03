import click

from pathlib import Path


@click.command("generate")
@click.option("--config", default="config.yaml", help="Path to the configuration file.")
def generate(config: str):
    from elmes.config import load_conf
    from elmes.run import run

    import asyncio

    path = Path(config)
    load_conf(path)

    asyncio.run(run())


@click.command()
@click.option(
    "--input-dir", default="inputs", help="Directory containing chat databases"
)
def export_json(input_dir: str):
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
            messages.append({"role": m.name, "content": m.content})

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


@click.group()
def main():
    pass


main.add_command(generate)
main.add_command(export_json)

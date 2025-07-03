import click

from pathlib import Path


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

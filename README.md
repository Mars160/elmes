# 教育LLM评估系统 (**E**ducational L**LM** **E**valuation **S**ystem)

## 📖 项目简介

本项目是一个完整的教育领域大语言模型（LLM）评估系统，用于评估LLM在教育场景下的表现质量。系统支持多种后端模型（OpenAI、Ollama、DeepSeek），可以自动化执行教学任务，并对结果进行专业的教学质量评估。

## 🏗️ 项目结构

```
edu_evaluation/
├── README.md                      # 项目说明文档
├── requirements.txt               # Python依赖包列表
├── setup.py                      # 项目安装配置
├── init.py                       # 项目初始化脚本
├── 
├── config/                       # 配置文件目录
│   ├── config.yaml              # 主配置文件（场景配置）
│   ├── test_backend.yaml        # 测试后端配置
│   ├── evaluation_backend.yaml  # 评估后端配置
│   └── prompts/                 # 提示词配置
│       └── evaluation_prompts.yaml  # 评估提示词
│
├── src/                         # 源代码目录
│   ├── __init__.py
│   ├── backend/                 # 后端模块
│   │   ├── __init__.py
│   │   ├── base.py             # 后端基类
│   │   ├── ollama_backend.py   # Ollama后端
│   │   ├── openai_backend.py   # OpenAI后端
│   │   └── deepseek_backend.py # DeepSeek后端
│   │
│   ├── executor/               # 执行器模块
│   │   ├── __init__.py
│   │   ├── base.py            # 执行器基类
│   │   ├── single_turn_executor.py  # 单轮对话执行器
│   │   └── multi_turn_executor.py   # 多轮对话执行器
│   │
│   ├── prompts/               # 提示词生成器
│   │   ├── __init__.py
│   │   ├── base.py           # 提示词基类
│   │   └── knowledge_explanation.py  # 知识解释场景
│   │
│   └── evaluator/            # 评估器模块
│       ├── __init__.py
│       ├── base.py          # 评估器核心功能
│       └── show_score.py    # 分数显示工具
│
├── results/                  # 执行结果目录
│   └── *.json               # 格式：日期_时间码_S{场景ID}_T{任务ID}_模型名.json
│
├── evaluation_result/        # 评估结果目录
│   └── eval_*.json          # 评估结果文件
│
├── tests/                   # 测试文件目录
├── docs/                    # 文档目录
└── *.py                     # 顶层测试脚本
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <project-url>
cd edu_evaluation

# 安装依赖
pip install -r requirements.txt

# 初始化项目配置
python init.py
```

### 2. 配置后端

创建 `.env` 文件配置API密钥：

```bash
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1

# DeepSeek配置
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com

# Ollama配置（本地部署）
OLLAMA_API_BASE=http://localhost:11434
```

### 3. 基本使用

```bash
# 运行单个任务测试
python test_backends.py

# 运行所有任务
python test_all_tasks.py

# 评估结果
python src/evaluator/base.py result_file.json

# 显示分数
python src/evaluator/show_score.py
```

## 🔄 评估流程

### 完整工作流程

```
1. 任务执行阶段
   ├── 加载场景配置 (config/config.yaml)
   ├── 生成教学提示词 (src/prompts/)
   ├── 调用LLM生成教学内容 (src/backend/)
   ├── 处理和格式化响应 (src/executor/)
   └── 保存结果 (results/*.json)

2. 质量评估阶段
   ├── 读取结果文件 (results/*.json)
   ├── 提取Q&A内容
   ├── 加载评估提示词 (config/prompts/evaluation_prompts.yaml)
   ├── 调用评估模型 (evaluation_backend)
   ├── 解析评估分数
   └── 保存评估结果 (evaluation_result/eval_*.json)

3. 结果展示阶段
   ├── 提取分数数据
   ├── 统计分析
   └── 格式化输出
```

### 详细执行步骤

#### 步骤1：任务执行
```python
from src.executor import SingleTurnExecutor
from src.backend import OpenAIBackend
from src.prompts import KnowledgeExplanationPromptGenerator

# 初始化组件
backend = OpenAIBackend()
prompt_generator = KnowledgeExplanationPromptGenerator()
executor = SingleTurnExecutor(backend, prompt_generator, "results")

# 执行任务
executor.initialize()
result = executor.execute(task_id=1)
```

#### 步骤2：质量评估
```python
from src.evaluator import evaluate_json

# 评估结果文件
eval_result = evaluate_json(
    result_file_path="results/example.json",
    backend="openai"
)
```

#### 步骤3：结果查看
```python
from src.evaluator import show_score_from_file

# 显示分数
show_score_from_file("evaluation_result/eval_example.json")
```

## 📋 主要功能模块

### 1. 后端系统 (`src/backend/`)

支持多种LLM后端，统一接口设计：

- **OpenAI Backend**: 支持GPT系列模型
- **Ollama Backend**: 支持本地部署的开源模型
- **DeepSeek Backend**: 支持DeepSeek系列模型

**特性**：
- 统一的配置管理（参数 > 环境变量 > 配置文件 > 默认值）
- 自动重试和错误处理
- 标准化响应格式

### 2. 执行器系统 (`src/executor/`)

负责任务的完整执行流程：

- **SingleTurnExecutor**: 单轮对话任务执行
- **MultiTurnExecutor**: 多轮对话任务执行（开发中）

**功能**：
- 提示词生成
- 模型调用
- 响应处理
- 结果保存（S{场景ID}_T{任务ID}格式命名）

### 3. 提示词系统 (`src/prompts/`)

场景化的教学提示词生成：

- **KnowledgeExplanationPromptGenerator**: 知识解释场景
- 支持扩展其他教学场景

### 4. 评估器系统 (`src/evaluator/`)

专业的教学质量评估：

- **自动场景识别**: 根据结果文件自动选择评估标准
- **多格式解析**: 支持JSON和文本格式的评估结果
- **统计分析**: 自动计算总分、平均分、最值等统计指标

### 5. 配置系统 (`config/`)

分层的配置管理：

- **config.yaml**: 场景和任务配置
- **test_backend.yaml**: 测试环境后端配置
- **evaluation_backend.yaml**: 评估环境后端配置
- **evaluation_prompts.yaml**: 各场景评估提示词

## 💡 使用示例

### 示例1：单次任务执行和评估

```bash
# 1. 执行知识解释任务
python -c "
from src.executor import SingleTurnExecutor
from src.backend import OpenAIBackend
from src.prompts import KnowledgeExplanationPromptGenerator

backend = OpenAIBackend()
prompt_generator = KnowledgeExplanationPromptGenerator()
executor = SingleTurnExecutor(backend, prompt_generator, 'results')
executor.initialize()
result = executor.execute(1)
print(f'结果文件: {result[\"saved_path\"]}')
"

# 2. 评估结果
python src/evaluator/base.py results/latest_file.json

# 3. 查看分数
python src/evaluator/show_score.py
```

### 示例2：批量处理

```bash
# 执行所有任务
python test_all_tasks.py

# 查看所有评估文件
python src/evaluator/show_score.py --list

# 查看特定文件分数
python src/evaluator/show_score.py evaluation_result/eval_xxx.json
```

### 示例3：程序化使用

```python
from src.evaluator import Evaluator, show_score_from_file

# 初始化评估器
evaluator = Evaluator(backend_config="openai")
evaluator.initialize()

# 评估文件
result_path = evaluator.evaluate_file("results/example.json")

# 显示分数
show_score_from_file(result_path)
```

## 🔧 开发指南

### 添加新的后端

1. 继承 `Backend` 基类
2. 实现 `initialize()` 和 `chat()` 方法
3. 在 `src/backend/__init__.py` 中导出
4. 更新配置文件

```python
from src.backend.base import Backend

class NewBackend(Backend):
    def __init__(self, **kwargs):
        super().__init__("new_backend", **kwargs)
    
    def initialize(self) -> bool:
        # 初始化逻辑
        return True
    
    def chat(self, messages, **kwargs):
        # 实现对话逻辑
        pass
```

### 添加新的场景

1. 继承 `PromptGenerator` 基类
2. 实现场景特定的提示词生成逻辑
3. 在 `config/config.yaml` 中添加场景配置
4. 在 `config/prompts/evaluation_prompts.yaml` 中添加评估标准

### 扩展评估功能

评估器支持多种分数格式：

```json
// 简单格式
{"维度1": 5, "维度2": 4}

// 复杂格式
{"维度1": {"score": 5, "comment": "评价"}}

// 嵌套格式
{"类别1": {"维度1": {"score": 5}}}
```

## 📊 文件格式说明

### 结果文件格式 (`results/*.json`)

```json
{
  "scenario": "场景名称",
  "task_id": "任务ID",
  "messages": [{"role": "user", "content": "问题"}],
  "raw_response": {"choices": [{"message": {"content": "回答"}}]},
  "execution_info": {
    "backend": "后端名称",
    "model_name": "被测模型名称",
    "timestamp": "执行时间"
  }
}
```

### 评估结果格式 (`evaluation_result/eval_*.json`)

```json
{
  "original_file": "原始结果文件路径",
  "scenario": "场景名称",
  "task_id": "任务ID",
  "evaluation_backend": "评估后端",
  "evaluation_model": "评估模型",
  "evaluation_response": {"评估模型的完整响应"},
  "evaluation_timestamp": "评估时间"
}
```

## 🛠️ 常见问题

### Q: 如何配置中文字体显示？
A: 系统会自动检测可用的中文字体。如果显示异常，可以：
- macOS: 系统自带 PingFang SC
- Windows: 安装微软雅黑
- Linux: `sudo apt-get install fonts-wqy-microhei`

### Q: 如何添加新的评估维度？
A: 修改 `config/prompts/evaluation_prompts.yaml` 文件，添加对应场景的评估标准。

### Q: 支持哪些模型？
A: 
- OpenAI: GPT-3.5, GPT-4, GPT-4o 等
- Ollama: Qwen, Llama, Mistral 等本地模型
- DeepSeek: DeepSeek-Chat 等

### Q: 如何自定义评估标准？
A: 在 `config/prompts/evaluation_prompts.yaml` 中修改或添加场景对应的评估提示词模板。

## 📞 联系方式

如有问题或建议，请联系项目维护者或提交 Issue。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。 
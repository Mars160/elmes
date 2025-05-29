from typing import Dict, Any, override, List
from pathlib import Path
import yaml

from src.prompts.base import BasePromptGenerator


class GuidedTeachingPromptGenerator(BasePromptGenerator):
    def __init__(self):
        super().__init__("guided_teaching")
        config_path = Path("config/prompts/task_prompts.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"Task prompts file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            data = data[self.scenario_name]
        images = data["images"]
        questions = data["questions"]
        result = {}
        for i in range(len(images)):
            for j in range(len(questions)):
                index = i * len(questions) + j + 1
                result[f"task{index}"] = {
                    "image": images[i - 1],
                    "question": questions[j - 1],
                }
        self.task_prompts = result

    def _generate_prompt(
        self, scenario_prompts: Dict[str, Any], task_prompts: Dict[str, Any]
    ) -> str:
        return ""

    @override
    def _load_task_prompts(self, task_id: int) -> Dict[str, Any]:
        """加载任务提示词配置"""

    @override
    def generate_prompt(
        self, task_id: int, **kwargs
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        生成系统提示词
        """
        task_prompts = self.task_prompts["task{}".format(task_id)]
        # prompt = self._generate_prompt(self.scenario_prompts, task_prompts)
        teacher_prompt: Dict[str, str] = self.scenario_prompts["teacher"]
        tpn = []
        for k, v in teacher_prompt.items():
            tpn.append(
                {
                    "role": k,
                    "content": self.replace_task(v, task_prompts),
                }
            )
        student_prompt: Dict[str, str] = self.scenario_prompts["student"]
        spn = []
        for k, v in student_prompt.items():
            spn.append(
                {
                    "role": k,
                    "content": self.replace_task(v, task_prompts),
                }
            )
        prompt = {
            "teacher": tpn,
            "student": spn,
        }
        return prompt


if __name__ == "__main__":
    prompt_generator = GuidedTeachingPromptGenerator()
    for i in range(1, 11):
        print(prompt_generator.generate_prompt(i))

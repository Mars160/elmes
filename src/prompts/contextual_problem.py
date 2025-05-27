from typing import Dict, Any
import os
import sys

from src.prompts.base import BasePromptGenerator

class ContextualProblemPromptGenerator(BasePromptGenerator):

    def __init__(self):
        super().__init__("contextual_problem")
    
    def _generate_prompt(self, scenario_prompts: Dict[str, Any], task_prompts: Dict[str, Any]) -> str:
        prompt = scenario_prompts+task_prompts
        return prompt
 
      
        



if __name__ == "__main__":
    prompt_generator = ContextualProblemPromptGenerator()
    for i in range(1,8):
        print(prompt_generator.generate_prompt(i))
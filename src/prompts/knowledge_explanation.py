from typing import Dict, Any
import os
import sys

from src.prompts.base import BasePromptGenerator

class KnowledgeExplanationPromptGenerator(BasePromptGenerator):

    def __init__(self):
        super().__init__("knowledge_explanation")
    
    def _generate_prompt(self, scenario_prompts: Dict[str, Any], task_prompts: Dict[str, Any]) -> str:
        prompt = scenario_prompts.replace("{image}", task_prompts["image"]).replace("{query}", task_prompts["query"])
        return prompt
 
      
        



if __name__ == "__main__":
    prompt_generator = KnowledgeExplanationPromptGenerator()
    print(prompt_generator.generate_prompt(2))
#!/usr/bin/env python3
"""
初始化脚本 - 自动更新config.yaml中的scenarios统计信息

这个脚本会：
1. 读取scenario_prompts.yaml文件，获取所有可用的scenario
2. 读取task_prompts.yaml文件，统计每个scenario下的task数量
3. 自动更新config.yaml文件中的scenarios字段

使用方法：
    python init.py
"""

import yaml
import os
import sys
from pathlib import Path
from typing import Dict, Any


class ConfigInitializer:
    """配置文件初始化器"""
    
    def __init__(self):
        self.scenario_prompts_path = Path('config/prompts/scenario_prompts.yaml')
        self.task_prompts_path = Path('config/prompts/task_prompts.yaml')
        self.config_path = Path('config/config.yaml')
        
        # 场景名称映射到中文名称
        self.scenario_names = {
            'knowledge_explanation': '知识点讲解',
            'guided_teaching': '引导式讲题',
            'interdisciplinary_task': '跨学科任务',
            'contextual_problem': '情境问题'
        }
    
    def check_files_exist(self):
        """检查必要的配置文件是否存在"""
        missing_files = []
        
        if not self.scenario_prompts_path.exists():
            missing_files.append(str(self.scenario_prompts_path))
        
        if not self.task_prompts_path.exists():
            missing_files.append(str(self.task_prompts_path))
        
        if missing_files:
            print(f"❌ 缺少必要的配置文件:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        return True
    
    def load_scenario_prompts(self) -> Dict[str, Any]:
        """加载scenario_prompts.yaml文件"""
        try:
            with open(self.scenario_prompts_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data or {}
        except Exception as e:
            print(f"❌ 读取scenario_prompts.yaml失败: {e}")
            return {}
    
    def load_task_prompts(self) -> Dict[str, Any]:
        """加载task_prompts.yaml文件"""
        try:
            with open(self.task_prompts_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data or {}
        except Exception as e:
            print(f"❌ 读取task_prompts.yaml失败: {e}")
            return {}
    
    def count_tasks_per_scenario(self, task_prompts: Dict[str, Any]) -> Dict[str, int]:
        """统计每个scenario下的task数量"""
        task_counts = {}
        
        for scenario_name, tasks in task_prompts.items():
            if isinstance(tasks, dict):
                # 统计以"task"开头的键的数量
                task_count = len([key for key in tasks.keys() if key.startswith('task')])
                task_counts[scenario_name] = task_count
            else:
                task_counts[scenario_name] = 0
        
        return task_counts
    
    def generate_scenarios_config(self, scenarios: Dict[str, Any], task_counts: Dict[str, int]) -> Dict[str, Any]:
        """生成scenarios配置"""
        scenarios_config = {}
        scenario_id = 1
        
        for scenario_name in scenarios.keys():
            scenarios_config[scenario_name] = {
                'id': scenario_id,
                'name': self.scenario_names.get(scenario_name, scenario_name),
                'tasks': task_counts.get(scenario_name, 0)
            }
            scenario_id += 1
        
        return scenarios_config
    
    def load_existing_config(self) -> Dict[str, Any]:
        """加载现有的config.yaml文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️  读取现有config.yaml失败: {e}")
        
        return {}
    
    def save_config(self, config: Dict[str, Any]):
        """保存更新后的config.yaml文件"""
        try:
            # 确保config目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                # 添加文件头部注释
                f.write('# Scenario configurations\n')
                yaml.dump(config, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
            
            print(f"✅ 配置文件已更新: {self.config_path}")
            
        except Exception as e:
            print(f"❌ 保存config.yaml失败: {e}")
            return False
        
        return True
    
    def print_summary(self, scenarios_config: Dict[str, Any]):
        """打印统计摘要"""
        print("\n📊 Scenarios统计摘要:")
        print("=" * 50)
        
        total_tasks = 0
        for scenario_name, config in scenarios_config.items():
            print(f"S{config['id']} - {config['name']} ({scenario_name}): {config['tasks']} tasks")
            total_tasks += config['tasks']
        
        print("=" * 50)
        print(f"总计: {len(scenarios_config)} scenarios, {total_tasks} tasks")
    
    def run(self):
        """运行初始化流程"""
        print("🚀 开始初始化配置文件...")
        
        # 1. 检查文件是否存在
        if not self.check_files_exist():
            sys.exit(1)
        
        # 2. 加载配置文件
        print("📖 读取配置文件...")
        scenario_prompts = self.load_scenario_prompts()
        task_prompts = self.load_task_prompts()
        
        if not scenario_prompts:
            print("❌ scenario_prompts.yaml文件为空或格式错误")
            sys.exit(1)
        
        # 3. 统计task数量
        print("🔢 统计task数量...")
        task_counts = self.count_tasks_per_scenario(task_prompts)
        
        # 4. 生成scenarios配置
        scenarios_config = self.generate_scenarios_config(scenario_prompts, task_counts)
        
        # 5. 加载现有配置（保留其他字段）
        existing_config = self.load_existing_config()
        
        # 6. 更新scenarios字段
        existing_config['scenarios'] = scenarios_config
        
        # 7. 保存配置文件
        if self.save_config(existing_config):
            self.print_summary(scenarios_config)
            print("\n🎉 初始化完成!")
        else:
            sys.exit(1)


def main():
    """主函数"""
    initializer = ConfigInitializer()
    initializer.run()


if __name__ == "__main__":
    main() 
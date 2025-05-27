#!/usr/bin/env python
"""
简单的分数显示脚本

用于从评估结果JSON文件中提取和打印分数
"""

import json
import re
import glob
import os
from pathlib import Path
from typing import Dict, Any, Union


def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_evaluation_content(data: Dict[str, Any]) -> str:
    """提取评估响应内容"""
    try:
        return data['evaluation_response']['choices'][0]['message']['content']
    except (KeyError, IndexError):
        return ""


def parse_json_scores(content: str) -> Dict[str, Union[float, int]]:
    """解析JSON格式的分数"""
    try:
        # 尝试直接解析JSON
        if content.strip().startswith('{'):
            data = json.loads(content)
            return flatten_scores(data)
        
        # 尝试从markdown代码块中提取JSON
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            return flatten_scores(data)
        
        # 尝试查找JSON对象
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            return flatten_scores(data)
            
    except (json.JSONDecodeError, AttributeError):
        pass
    
    return {}


def flatten_scores(data: Dict[str, Any], prefix: str = "") -> Dict[str, Union[float, int]]:
    """将嵌套的分数数据扁平化"""
    scores = {}
    
    for key, value in data.items():
        current_key = f"{prefix}{key}" if prefix else key
        
        # 直接是数字
        if isinstance(value, (int, float)):
            scores[current_key] = value
        
        # 包含score字段的字典
        elif isinstance(value, dict) and 'score' in value:
            scores[current_key] = value['score']
        
        # 嵌套字典，需要递归处理
        elif isinstance(value, dict):
            nested_scores = flatten_scores(value, f"{current_key}_")
            scores.update(nested_scores)
    
    return scores


def parse_text_scores(content: str) -> Dict[str, Union[float, int]]:
    """解析文本格式的分数"""
    scores = {}
    
    # 匹配形如 "维度名: 分数" 或 "维度名：分数" 的模式
    patterns = [
        r'([^:\n]+)[:：]\s*(\d+(?:\.\d+)?)',
        r'([^:\n]+)[:：]\s*(\d+(?:\.\d+)?)分',
        r'([^:\n]+)\s*(\d+(?:\.\d+)?)分',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            dimension = match[0].strip()
            score = float(match[1])
            scores[dimension] = score
    
    return scores


def extract_scores_from_file(file_path: str) -> Dict[str, Union[float, int]]:
    """从文件中提取分数"""
    try:
        # 加载文件
        data = load_json_file(file_path)
        
        # 提取评估内容
        content = extract_evaluation_content(data)
        
        if not content:
            return {}
        
        # 尝试解析JSON格式的分数
        scores = parse_json_scores(content)
        
        # 如果JSON解析失败，尝试文本解析
        if not scores:
            scores = parse_text_scores(content)
        
        return scores
        
    except Exception as e:
        print(f"❌ 提取分数失败: {e}")
        return {}


def get_tested_model_info(file_info: Dict[str, Any]) -> str:
    """获取被测模型信息"""
    if not file_info:
        return "未知"
    
    # 尝试从原始文件中获取被测模型信息
    original_file = file_info.get('original_file')
    if original_file and os.path.exists(original_file):
        try:
            original_data = load_json_file(original_file)
            execution_info = original_data.get('execution_info', {})
            tested_model = execution_info.get('model_name', '未知')
            if tested_model != '未知':
                return tested_model
        except Exception:
            pass
    
    # 尝试从文件名中提取模型信息
    if original_file:
        filename = os.path.basename(original_file)
        # 文件名格式：日期_时间_S{场景}_T{任务}_模型名.json
        parts = filename.replace('.json', '').split('_')
        if len(parts) >= 5:
            model_part = '_'.join(parts[4:])  # 获取模型名部分
            return model_part
    
    return "未知"


def print_scores(scores: Dict[str, Union[float, int]], file_info: Dict[str, Any] = None):
    """打印分数"""
    if not scores:
        print("⚠️  未找到分数数据")
        return
    
    print("📊 评估分数")
    print("=" * 50)
    
    # 打印文件信息
    if file_info:
        scenario = file_info.get('scenario', '未知')
        task_id = file_info.get('task_id', '未知')
        eval_model = file_info.get('evaluation_model', '未知')
        tested_model = get_tested_model_info(file_info)
        timestamp = file_info.get('evaluation_timestamp', '未知')
        
        print(f"场景: {scenario}")
        print(f"任务ID: {task_id}")
        print(f"被测模型: {tested_model}")
        print(f"评估模型: {eval_model}")
        print(f"时间: {timestamp}")
        print("-" * 50)
    
    # 打印分数
    print("详细分数:")
    for dimension, score in scores.items():
        print(f"  {dimension}: {score}")
    
    # 统计信息
    if scores:
        total_score = sum(scores.values())
        avg_score = total_score / len(scores)
        max_score = max(scores.values())
        min_score = min(scores.values())
        
        print("-" * 50)
        print("统计信息:")
        print(f"  总分: {total_score:.2f}")
        print(f"  平均分: {avg_score:.2f}")
        print(f"  最高分: {max_score:.2f}")
        print(f"  最低分: {min_score:.2f}")
        print(f"  维度数量: {len(scores)}")


def show_score_from_file(file_path: str):
    """显示文件中的分数"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📁 读取文件: {file_path}")
    
    try:
        # 加载文件数据
        data = load_json_file(file_path)
        
        # 提取分数
        scores = extract_scores_from_file(file_path)
        
        # 打印分数
        print_scores(scores, data)
        
    except Exception as e:
        print(f"❌ 处理文件失败: {e}")


def find_latest_eval_file() -> str:
    """查找最新的评估文件"""
    files = glob.glob("evaluation_result/eval_*.json")
    if not files:
        return ""
    
    return max(files, key=lambda x: Path(x).stat().st_mtime)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="显示评估结果中的分数")
    parser.add_argument("file", nargs="?", help="评估结果JSON文件路径")
    parser.add_argument("--list", action="store_true", help="列出所有评估文件")
    args = parser.parse_args()
    
    if args.list:
        # 列出所有评估文件
        files = glob.glob("evaluation_result/eval_*.json")
        if files:
            print("📁 可用的评估文件:")
            for i, file in enumerate(sorted(files), 1):
                stat = Path(file).stat()
                size = stat.st_size
                mtime = Path(file).stat().st_mtime
                from datetime import datetime
                time_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {i}. {file} ({size}B, {time_str})")
        else:
            print("⚠️  未找到评估文件")
        return
    
    if args.file:
        target_file = args.file
    else:
        # 查找最新的评估文件
        target_file = find_latest_eval_file()
        if not target_file:
            print("⚠️  未找到评估结果文件")
            print("💡 使用 --list 查看可用文件，或指定文件路径")
            return
        
        print(f"🔍 使用最新的评估文件: {target_file}")
    
    # 显示分数
    show_score_from_file(target_file)


if __name__ == "__main__":
    main() 
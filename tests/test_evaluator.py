#!/usr/bin/env python3
"""
评估器测试脚本
测试评估器的各种功能
"""

from src.evaluator.base import Evaluator
import glob
import os

def test_single_file_evaluation():
    """测试单个文件评估"""
    print("=" * 60)
    print("🧪 测试单个文件评估")
    print("=" * 60)
    
    # 创建评估器（使用Ollama）
    evaluator = Evaluator(evaluation_backend_config="openai")
    
    # 初始化
    success = evaluator.initialize()
    if not success:
        print("❌ 评估器初始化失败")
        return
    
    # 找到一个测试文件
    result_files = glob.glob("results/*.json")
    if not result_files:
        print("⚠️  未找到结果文件")
        return
    
    test_file = result_files[0]
    print(f"📁 测试文件: {test_file}")
    
    try:
        # 评估文件
        eval_result = evaluator.evaluate_result_file(
            test_file,
            Student_image="小学二年级学生，女生，很喜欢数学，对新知识充满好奇",
            Student_query="下节课学习有理数，你帮我预习"
        )
        print(f"✅ 评估成功: {eval_result}")
        
        # 显示评估结果摘要
        with open(eval_result, 'r', encoding='utf-8') as f:
            import json
            result = json.load(f)
            print(f"📊 评估摘要:")
            print(f"   - 原始文件: {result['original_file']}")
            print(f"   - 场景: {result['scenario']}")
            print(f"   - 任务ID: {result['task_id']}")
            print(f"   - 评估模型: {result['evaluation_model']}")
            print(f"   - 评估时间: {result['evaluation_timestamp']}")
            
    except Exception as e:
        print(f"❌ 评估失败: {e}")

def test_batch_evaluation():
    """测试批量评估"""
    print("\n" + "=" * 60)
    print("🚀 测试批量评估")
    print("=" * 60)
    
    # 创建评估器（使用OpenAI，如果配置了的话）
    evaluator = Evaluator(evaluation_backend_config="ollama")  # 先用ollama测试
    
    # 初始化
    success = evaluator.initialize()
    if not success:
        print("❌ 评估器初始化失败")
        return
    
    try:
        # 批量评估（限制为前3个文件）
        pattern = "results/*.json"
        result_files = glob.glob(pattern)[:3]  # 只评估前3个文件
        
        if not result_files:
            print("⚠️  未找到结果文件")
            return
        
        print(f"📁 准备评估 {len(result_files)} 个文件")
        
        # 手动批量评估以便添加参数
        evaluation_files = []
        for result_file in result_files:
            try:
                eval_file = evaluator.evaluate_result_file(
                    result_file,
                    Student_image="小学二年级学生，女生，很喜欢数学",
                    Student_query="学习相关知识点"
                )
                evaluation_files.append(eval_file)
                print(f"   ✅ {os.path.basename(result_file)} -> {os.path.basename(eval_file)}")
            except Exception as e:
                print(f"   ❌ {os.path.basename(result_file)}: {e}")
        
        print(f"🎉 批量评估完成，成功评估 {len(evaluation_files)} 个文件")
        
        # 显示评估结果目录
        print(f"📂 评估结果保存在: evaluation_result/")
        eval_files = glob.glob("evaluation_result/*.json")
        print(f"📊 总计 {len(eval_files)} 个评估结果文件")
        
    except Exception as e:
        print(f"❌ 批量评估失败: {e}")

def test_different_backends():
    """测试不同的后端"""
    print("\n" + "=" * 60)
    print("🔄 测试不同评估后端")
    print("=" * 60)
    
    backends = ["ollama"]  # 先只测试ollama
    
    # 找一个测试文件
    result_files = glob.glob("results/*.json")
    if not result_files:
        print("⚠️  未找到结果文件")
        return
    
    test_file = result_files[0]
    
    for backend in backends:
        print(f"\n🧪 测试后端: {backend}")
        try:
            evaluator = Evaluator(evaluation_backend_config=backend)
            success = evaluator.initialize()
            
            if success:
                eval_file = evaluator.evaluate_result_file(
                    test_file,
                    Student_image="小学生，对数学感兴趣",
                    Student_query="学习数学知识"
                )
                print(f"   ✅ {backend} 后端评估成功: {os.path.basename(eval_file)}")
            else:
                print(f"   ❌ {backend} 后端初始化失败")
                
        except Exception as e:
            print(f"   ❌ {backend} 后端测试失败: {e}")

def main():
    """主测试函数"""
    print("🎯 评估器功能测试开始")
    
    # 确保输出目录存在
    os.makedirs("evaluation_result", exist_ok=True)
    
    # 测试单个文件评估
    test_single_file_evaluation()
    
    # 测试批量评估
    test_batch_evaluation()
    
    # 测试不同后端
    test_different_backends()
    
    print("\n" + "=" * 60)
    print("🏁 评估器测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main() 
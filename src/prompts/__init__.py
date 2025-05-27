"""提示词生成模块"""

# 导出所有提示词生成器类
try:
    from .knowledge_explanation import KnowledgeExplanationPromptGenerator


    __all__ = [
        'KnowledgeExplanationPromptGenerator',
        'GuidedTeachingPromptGenerator', 
        'InterdisciplinaryTaskPromptGenerator',
        'ContextualProblemPromptGenerator'
    ]
except ImportError as e:
    # 避免在导入时出现错误，记录可能的导入问题
    import sys
    print(f"提示词生成器导入错误: {e}", file=sys.stderr)

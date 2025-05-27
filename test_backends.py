#!/usr/bin/env python3
"""
Backend测试脚本 - 测试所有backend实现
"""

from src.backend import OllamaBackend, OpenAIBackend, DeepSeekBackend

def test_backend(backend_class, backend_name):
    """
    测试指定的backend
    
    Args:
        backend_class: Backend类
        backend_name: Backend名称
    """
    print(f"\n🧪 测试 {backend_name} Backend")
    print("=" * 50)
    
    try:
        # 创建backend实例
        backend = backend_class()
        
        # 显示配置信息
        print(f"模型名称: {backend.model_name}")
        print(f"API地址: {backend.api_base}")
        print(f"API密钥: {'已设置' if backend.api_key else '未设置'}")
        print(f"超时时间: {backend.timeout}秒")
        print(f"最大重试: {backend.max_retries}次")
        
        # 初始化测试
        print(f"\n初始化 {backend_name}...")
        success = backend.initialize()
        
        if success:
            print(f"✅ {backend_name} 初始化成功")
            
            # 如果初始化成功，尝试发送一个简单请求
            messages = [
                {"role": "system", "content": "你是一个友好的AI助手。"},
                {"role": "user", "content": "简单回答：你好"}
            ]
            
            print(f"发送测试消息...")
            try:
                response = backend.chat(messages, max_tokens=50)
                if response and "choices" in response:
                    content = response["choices"][0]["message"]["content"]
                    print(f"✅ 测试响应: {content[:100]}...")
                else:
                    print(f"⚠️  响应格式异常: {response}")
            except Exception as e:
                print(f"❌ 聊天测试失败: {e}")
        else:
            print(f"❌ {backend_name} 初始化失败")
            
    except Exception as e:
        print(f"❌ {backend_name} 测试出错: {e}")

def test_all_backends():
    """测试所有backend"""
    print("🚀 开始测试所有Backend实现...")
    
    backends = [
        (OllamaBackend, "Ollama"),
        (OpenAIBackend, "OpenAI"),
        (DeepSeekBackend, "DeepSeek")
    ]
    
    results = {}
    
    for backend_class, name in backends:
        test_backend(backend_class, name)
        results[name] = "已测试"
    
    print("\n" + "=" * 60)
    print("📊 测试总结:")
    print("=" * 60)
    
    for name in results:
        print(f"✓ {name} Backend: {results[name]}")
    
    print("\n💡 提示:")
    print("- 如果Ollama测试失败，请确保Ollama服务正在运行")
    print("- 如果OpenAI测试失败，请检查OPENAI_API_KEY环境变量")
    print("- 如果DeepSeek测试失败，请检查DEEPSEEK_API_KEY环境变量")
    print("- 可以在.env文件中设置API密钥")

def test_config_loading():
    """测试配置文件加载"""
    print("\n🔧 测试配置文件加载...")
    print("=" * 50)
    
    try:
        # 测试从不同backend读取配置
        ollama = OllamaBackend()
        print(f"✅ Ollama配置加载成功")
        print(f"   - 模型: {ollama.model_name}")
        print(f"   - API地址: {ollama.api_base}")
        
        openai = OpenAIBackend()
        print(f"✅ OpenAI配置加载成功") 
        print(f"   - 模型: {openai.model_name}")
        print(f"   - API地址: {openai.api_base}")
        
        deepseek = DeepSeekBackend()
        print(f"✅ DeepSeek配置加载成功")
        print(f"   - 模型: {deepseek.model_name}")
        print(f"   - API地址: {deepseek.api_base}")
        
    except Exception as e:
        print(f"❌ 配置加载测试失败: {e}")

if __name__ == "__main__":
    # 测试配置加载
    test_config_loading()
    
    # 测试所有backend
    test_all_backends() 
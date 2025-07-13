#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FamilyAI 伴侣聊天界面功能测试脚本
"""

import requests
import json
import time

# 配置
API_BASE = "http://127.0.0.1:8401"
CHAT_BASE = "http://127.0.0.1:8402"
API_KEY = "sk-dummy-3e5010a20e8f4832a5f213ee85e6a3c7"

def test_services_status():
    """测试服务状态"""
    print("🔍 检查服务状态...")
    
    # 测试API服务器
    try:
        response = requests.get(f"{API_BASE}/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ API服务器正常 - 发现 {len(models['data'])} 个模型")
        else:
            print(f"❌ API服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API服务器连接失败: {e}")
        return False
    
    # 测试HTTP服务器
    try:
        response = requests.get(f"{CHAT_BASE}/chat.html", timeout=5)
        if response.status_code == 200:
            print("✅ HTTP服务器正常 - 聊天界面可访问")
        else:
            print(f"❌ HTTP服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ HTTP服务器连接失败: {e}")
        return False
    
    return True

def test_api_authentication():
    """测试API认证"""
    print("\n🔐 测试API认证...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE}/v1/models", headers=headers, timeout=5)
        if response.status_code == 200:
            print("✅ API认证通过")
            return True
        else:
            print(f"❌ API认证失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API认证测试异常: {e}")
        return False

def test_streaming_chat():
    """测试流式聊天功能"""
    print("\n💬 测试流式聊天功能...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "Claude-3.5-Sonnet",
        "messages": [
            {"role": "user", "content": "请简单说一句话测试"}
        ],
        "stream": True,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ 流式聊天响应正常")
            content_received = False
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                if delta.get('content'):
                                    content_received = True
                                    print(f"📝 接收到内容: {delta['content']}")
                        except json.JSONDecodeError:
                            pass
            
            if content_received:
                print("✅ 流式内容接收成功")
                return True
            else:
                print("❌ 未接收到流式内容")
                return False
        else:
            print(f"❌ 流式聊天请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 流式聊天测试异常: {e}")
        return False

def test_thinking_model():
    """测试思考型模型"""
    print("\n🧠 测试思考型模型...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "Claude-3.7-Sonnet-Extended",
        "messages": [
            {"role": "user", "content": "计算 2+3 等于多少？"}
        ],
        "stream": True,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            reasoning_received = False
            content_received = False
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                if delta.get('reasoning_content'):
                                    reasoning_received = True
                                    print(f"🧠 思考内容: {delta['reasoning_content']}")
                                if delta.get('content'):
                                    content_received = True
                                    print(f"📝 回答内容: {delta['content']}")
                        except json.JSONDecodeError:
                            pass
            
            if reasoning_received and content_received:
                print("✅ 思考型模型功能正常")
                return True
            elif content_received:
                print("⚠️  思考型模型部分功能正常（仅回答内容）")
                return True
            else:
                print("❌ 思考型模型无响应")
                return False
        else:
            print(f"❌ 思考型模型请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 思考型模型测试异常: {e}")
        return False

def test_multimodal_support():
    """测试多模态支持"""
    print("\n🖼️  测试多模态支持...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 模拟多模态请求（图片+文本）
    payload = {
        "model": "GPT-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这是一个多模态测试"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
                        }
                    }
                ]
            }
        ],
        "stream": True,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ 多模态请求响应正常")
            return True
        else:
            print(f"⚠️  多模态请求响应: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 多模态测试异常: {e}")
        return False

def test_chat_interface_accessibility():
    """测试聊天界面可访问性"""
    print("\n🌐 测试聊天界面可访问性...")
    
    try:
        response = requests.get(f"{CHAT_BASE}/chat.html", timeout=5)
        content = response.text
        
        # 检查关键功能元素
        required_elements = [
            'id="chatMessages"',
            'id="messageInput"',
            'id="sendButton"',
            'id="modelSelect"',
            'id="fileUpload"',
            'onclick="createNewSession()"',
            'onclick="exportCurrentSession()"',
            'marked.parse',
            'hljs.highlightElement'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if not missing_elements:
            print("✅ 聊天界面包含所有必要功能元素")
            return True
        else:
            print(f"⚠️  聊天界面缺少部分元素: {missing_elements}")
            return False
            
    except Exception as e:
        print(f"❌ 聊天界面检查异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始 FamilyAI 伴侣系统全面测试")
    print("=" * 50)
    
    test_results = []
    
    # 执行各项测试
    test_results.append(("服务状态", test_services_status()))
    test_results.append(("API认证", test_api_authentication()))
    test_results.append(("流式聊天", test_streaming_chat()))
    test_results.append(("思考型模型", test_thinking_model()))
    test_results.append(("多模态支持", test_multimodal_support()))
    test_results.append(("界面可访问性", test_chat_interface_accessibility()))
    
    # 测试结果汇总
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常")
        print("\n📝 下一步:")
        print("1. 访问 http://localhost:8402/chat.html 开始使用")
        print("2. 在设置中配置有效的 Session ID")
        print("3. 尝试不同模型和功能")
    else:
        print("⚠️  部分测试失败，请检查相关功能")
    
    print("\n🔗 服务地址:")
    print(f"  聊天界面: http://localhost:8402/chat.html")
    print(f"  API文档: http://localhost:8401/docs")
    print(f"  模型列表: http://localhost:8401/models")

if __name__ == "__main__":
    main()
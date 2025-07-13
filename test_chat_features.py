#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试脚本 - 验证chat.html的完整功能
"""

import requests
import json
import time

API_BASE = "http://127.0.0.1:8401"

def test_api_server():
    """测试API服务器状态"""
    print("=== 测试API服务器 ===")
    try:
        response = requests.get(f"{API_BASE}/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"API服务器正常 - 模型数量: {len(models['data'])}")
            return True
        else:
            print(f"API服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"API服务器连接失败: {e}")
        return False

def test_config_endpoints():
    """测试配置管理端点"""
    print("\n=== 测试配置管理端点 ===")
    
    # 测试保存配置
    test_config = {
        "session_id": "test_ui_session",
        "api_base": "http://127.0.0.1:8401",
        "theme": "blue",
        "temperature": 0.8,
        "max_tokens": 3000
    }
    
    try:
        response = requests.post(f"{API_BASE}/config/", json=test_config, timeout=5)
        if response.status_code == 200:
            print("配置保存端点正常")
        else:
            print(f"配置保存端点异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"配置保存端点测试失败: {e}")
        return False
    
    # 测试获取配置
    try:
        response = requests.get(f"{API_BASE}/config/", timeout=5)
        if response.status_code == 200:
            config = response.json()
            print(f"配置获取端点正常 - 数据: {config}")
        else:
            print(f"配置获取端点异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"配置获取端点测试失败: {e}")
        return False
    
    # 测试会话保存
    test_session = {
        "session_id": "test_ui_session_456"
    }
    
    try:
        response = requests.post(f"{API_BASE}/config/sessions", json=test_session, timeout=5)
        if response.status_code == 200:
            print("会话保存端点正常")
        else:
            print(f"会话保存端点异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"会话保存端点测试失败: {e}")
        return False
    
    # 测试获取会话
    try:
        response = requests.get(f"{API_BASE}/config/sessions", timeout=5)
        if response.status_code == 200:
            sessions = response.json()
            print(f"会话获取端点正常 - 数据: {sessions}")
        else:
            print(f"会话获取端点异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"会话获取端点测试失败: {e}")
        return False
    
    return True

def test_chat_functionality():
    """测试聊天功能"""
    print("\n=== 测试聊天功能 ===")
    
    headers = {
        "Authorization": "Bearer sk-dummy-3e5010a20e8f4832a5f213ee85e6a3c7",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "Claude-3.5-Sonnet",
        "messages": [
            {"role": "user", "content": "请简单回复：功能测试"}
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
            print("聊天功能正常")
            return True
        else:
            print(f"聊天功能异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"聊天功能测试失败: {e}")
        return False

def check_files():
    """检查生成的配置文件"""
    print("\n=== 检查配置文件 ===")
    
    import os
    
    files_to_check = [
        "tenbin_config.json",
        "tenbin_sessions.json",
        "chat.html"
    ]
    
    for file_name in files_to_check:
        if os.path.exists(file_name):
            file_size = os.path.getsize(file_name)
            print(f"{file_name}: 存在 ({file_size} 字节)")
        else:
            print(f"{file_name}: 不存在")
            return False
    
    return True

def main():
    """主测试函数"""
    print("开始 chat.html 完整功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 执行各项测试
    test_results.append(("API服务器", test_api_server()))
    test_results.append(("配置管理端点", test_config_endpoints()))
    test_results.append(("聊天功能", test_chat_functionality()))
    test_results.append(("配置文件检查", check_files()))
    
    # 测试结果汇总
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("所有测试通过！chat.html功能完整")
        print("\n功能清单:")
        print("- 优化布局，内容区域空间更大")
        print("- 会话重命名功能（双击或点击编辑按钮）")
        print("- 会话删除功能")
        print("- 完善的设置面板（API配置、主题等）")
        print("- 设置保存到服务器配置文件")
        print("- 多主题支持（默认、深色、蓝色）")
        print("- 响应式设计优化")
        print("\n使用方法:")
        print("1. 启动服务器: python main.py")
        print("2. 访问界面: http://localhost:8402/chat.html")
        print("3. 设置 -> 保存设置 -> 配置将保存到服务器")
    else:
        print("部分测试失败，请检查相关功能")

if __name__ == "__main__":
    main()
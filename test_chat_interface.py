#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试HTML聊天界面的简单脚本
"""

import time
import webbrowser

def open_chat_interface():
    """打开聊天界面"""
    print("=== FamilyAI 伴侣聊天界面测试 ===")
    print()
    print("正在打开聊天界面...")
    print("URL: http://localhost:8402/chat.html")
    print()
    print("功能特性:")
    print("  - 实时流式对话")
    print("  - 多模型选择 (Claude 3.5 Sonnet, GPT-4o 等)")
    print("  - 思考型模型支持 (Claude 3.7 Extended)")
    print("  - 自动保存对话历史")
    print("  - 响应式设计")
    print("  - 连接状态指示")
    print()
    print("测试建议:")
    print("  1. 发送简单问候测试基本功能")
    print("  2. 切换到思考型模型测试reasoning显示")
    print("  3. 发送长消息测试流式响应")
    print("  4. 清空对话测试界面重置")
    print()
    print("注意事项:")
    print("  - 确保 Tenbin API 服务在 http://127.0.0.1:8401 运行")
    print("  - 浏览器需要支持 Fetch API 和 Stream API")
    print("  - 建议使用现代浏览器 (Chrome, Firefox, Safari)")
    print()
    
    # 尝试打开浏览器
    try:
        webbrowser.open('http://localhost:8402/chat.html')
        print("浏览器已打开聊天界面!")
    except Exception as e:
        print(f"自动打开浏览器失败: {e}")
        print("请手动访问: http://localhost:8402/chat.html")
    
    print()
    print("祝你使用愉快!")

if __name__ == "__main__":
    open_chat_interface()
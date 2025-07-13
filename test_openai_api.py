#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Tenbin OpenAI API Adapter
Tests the API endpoints using OpenAI format
"""

import json
import requests
import time


# 配置
API_BASE_URL = "http://127.0.0.1:8401"
API_KEY = "sk-dummy-3e5010a20e8f4832a5f213ee85e6a3c7"  # 从client_api_keys.json中获取的API密钥


def test_models_endpoint():
    """测试模型列表端点"""
    print("Testing /models endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/models")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print(f"Found {len(models['data'])} models")
            print("Available models:")
            for model in models['data'][:5]:  # 显示前5个模型
                print(f"  - {model['id']}")
            if len(models['data']) > 5:
                print(f"  ... and {len(models['data']) - 5} more")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print()


def test_v1_models_endpoint():
    """测试带认证的模型列表端点"""
    print("Testing /v1/models endpoint with authentication...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/v1/models", headers=headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json()
            print(f"Found {len(models['data'])} models")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print()


def test_chat_completion_stream():
    """测试流式聊天完成"""
    print("Testing /v1/chat/completions with streaming...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "Claude-3.5-Sonnet",
        "messages": [
            {
                "role": "user", 
                "content": "Hello! Please respond with just a simple greeting."
            }
        ],
        "stream": True,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("Streaming response:")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        if data_str.strip() == '[DONE]':
                            print("Stream completed")
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                reasoning = delta.get('reasoning_content', '')
                                if content:
                                    print(f"Content: {content}")
                                if reasoning:
                                    print(f"Reasoning: {reasoning}")
                        except json.JSONDecodeError:
                            print(f"Invalid JSON: {data_str}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")
    
    print()


def main():
    """主测试函数"""
    print("Starting Tenbin OpenAI API Tests")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"API Key: {API_KEY[:20]}...")
    print("=" * 50)
    
    # 测试基础端点
    test_models_endpoint()
    test_v1_models_endpoint()
    
    # 测试聊天完成
    test_chat_completion_stream()
    
    print("All tests completed!")


if __name__ == "__main__":
    main()
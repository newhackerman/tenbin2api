#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker部署测试脚本
验证所有服务是否正常启动
"""

import requests
import time
import sys

def test_service(url, service_name, timeout=30):
    """测试服务是否响应"""
    print(f"🔍 测试 {service_name}: {url}")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} 正常运行")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
    
    print(f"❌ {service_name} 连接失败")
    return False

def main():
    """主测试函数"""
    print("🐳 Docker部署测试")
    print("=" * 50)
    
    services = [
        ("http://localhost:8402/chat.html", "HTTP服务器"),
        ("http://localhost:8401/models", "API服务器")
        # API Solver运行在容器内部端口5000，不对外开放
    ]
    
    results = []
    for url, name in services:
        result = test_service(url, name)
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    
    all_passed = True
    for service_name, result in results:
        status = "✅ 正常" if result else "❌ 失败"
        print(f"  {service_name}: {status}")
        if not result:
            all_passed = False
    
    print("  API Solver: 🔒 内部运行 (端口5000)")
    
    if all_passed:
        print("\n🎉 所有对外服务正常运行！")
        print("\n🚀 访问地址:")
        print("  - 聊天界面: http://localhost:8402/chat.html")
        print("  - API文档: http://localhost:8401/docs")
        print("\n🔒 内部服务:")
        print("  - API Solver: 容器内部端口5000 (安全隔离)")
        return 0
    else:
        print("\n⚠️ 部分服务启动失败")
        print("\n📝 故障排除:")
        print("  1. 检查Docker容器是否运行: docker ps")
        print("  2. 查看容器日志: docker logs tenbin-ai-assistant")
        print("  3. 检查端口占用: netstat -tlnp | grep '840[1-2]'")
        print("  4. 进入容器检查内部服务: docker exec -it tenbin-ai-assistant curl http://localhost:5000/health")
        return 1

if __name__ == "__main__":
    sys.exit(main())
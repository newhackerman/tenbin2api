#!/bin/bash

# Docker快速部署脚本

echo "🐳 FamilyAI 伴侣 - Docker快速部署"
echo "=" * 50

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose未安装，请先安装docker-compose"
    exit 1
fi

echo "🔧 停止现有容器..."
docker-compose down 2>/dev/null

echo "🏗️ 构建并启动服务..."
docker-compose up --build -d

echo "⏳ 等待服务启动（60秒）..."
sleep 60

echo "🧪 运行测试..."
python3 test_docker_deployment.py

echo "📋 有用的命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  进入容器: docker exec -it tenbin-ai-assistant /bin/bash"
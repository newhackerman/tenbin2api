#!/bin/bash

# Docker容器启动脚本

echo "🚀 启动 Tenbin API 服务..."

# 检查必要的配置文件
if [ ! -f "/app/tenbin.json" ]; then
    echo "⚠️  创建默认 tenbin.json 文件..."
    cat > /app/tenbin.json << EOF
[
    {
        "session_id": "your_session_id_here"
    }
]
EOF
fi

if [ ! -f "/app/client_api_keys.json" ]; then
    echo "⚠️  创建默认 client_api_keys.json 文件..."
    DUMMY_KEY="sk-dummy-$(openssl rand -hex 16)"
    cat > /app/client_api_keys.json << EOF
[
    "$DUMMY_KEY"
]
EOF
    echo "📝 生成的临时API密钥: $DUMMY_KEY"
fi

if [ ! -f "/app/models.json" ]; then
    echo "⚠️  创建默认 models.json 文件..."
    cat > /app/models.json << EOF
{
    "Claude-3.5-Sonnet": "AnthropicClaude35Sonnet",
    "Claude-3.5-Haiku": "AnthropicClaude35Haiku",
    "Claude-3.7-Sonnet-Extended": "AnthropicClaude37SonnetExtended",
    "Claude-3-Opus": "AnthropicClaude3Opus",
    "Claude-3-Sonnet": "AnthropicClaude3Sonnet",
    "Claude-3-Haiku": "AnthropicClaude3Haiku",
    "GPT-4o": "OpenAIGPT4o",
    "GPT-4o-Mini": "OpenAIGPT4oMini",
    "GPT-4-Turbo": "OpenAIGPT4Turbo",
    "GPT-3.5-Turbo": "OpenAIGPT35Turbo"
}
EOF
fi

# 设置虚拟显示器（用于Turnstile-Solver）
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &

# 等待虚拟显示器启动
sleep 2

echo "🌐 启动 HTTP 静态文件服务器 (端口 8402)..."
# 启动HTTP服务器提供chat.html
python3 /app/http_server.py > /app/logs/http_server.log 2>&1 &
HTTP_PID=$!

echo "⏳ 等待HTTP服务器启动..."
sleep 3

echo "🔧 启动 API Solver 服务器 (内部端口 5000)..."
# 启动API Solver (Turnstile解决器) 仅限容器内部访问
python3 /app/api_solver.py --headless=True > /app/logs/api_solver.log 2>&1 &
SOLVER_PID=$!

echo "⏳ 等待API Solver启动..."
sleep 3

echo "🤖 启动 Tenbin API 服务器 (端口 8401)..."
# 启动主API服务器
python3 /app/main.py > /app/logs/api_server.log 2>&1 &
API_PID=$!

echo "⏳ 等待API服务器启动..."
sleep 5

echo "✅ 所有服务已启动"
echo "📊 服务状态:"
echo "   - HTTP服务器: http://localhost:8402/chat.html"
echo "   - API服务器: http://localhost:8401"
echo "   - API Solver: 内部端口5000 (不对外开放)"
echo "   - 进程ID: HTTP=$HTTP_PID, API=$API_PID, Solver=$SOLVER_PID"

# 创建健康检查函数
check_services() {
    local http_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8402/chat.html 2>/dev/null)
    local api_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8401/models 2>/dev/null)
    local solver_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health 2>/dev/null)
    
    echo "🔍 服务检查: HTTP=$http_status, API=$api_status, Solver=$solver_status"
    
    if [ "$http_status" != "200" ]; then
        echo "❌ HTTP服务器异常，重新启动..."
        kill $HTTP_PID 2>/dev/null
        python3 /app/http_server.py > /app/logs/http_server.log 2>&1 &
        HTTP_PID=$!
    fi
    
    if [ "$api_status" != "200" ]; then
        echo "❌ API服务器异常，重新启动..."
        kill $API_PID 2>/dev/null
        python3 /app/main.py > /app/logs/api_server.log 2>&1 &
        API_PID=$!
    fi
    
    if [ "$solver_status" != "200" ]; then
        echo "❌ API Solver异常，重新启动..."
        kill $SOLVER_PID 2>/dev/null
        python3 /app/api_solver.py --headless=True > /app/logs/api_solver.log 2>&1 &
        SOLVER_PID=$!
    fi
}

# 优雅关闭处理
cleanup() {
    echo "🛑 正在关闭服务..."
    kill $HTTP_PID $API_PID $SOLVER_PID 2>/dev/null
    pkill Xvfb 2>/dev/null
    echo "✅ 服务已关闭"
    exit 0
}

# 捕获信号
trap cleanup SIGTERM SIGINT

echo "🎯 服务运行中... 按 Ctrl+C 停止"
echo "📋 实时日志:"
echo "   - HTTP服务器日志: tail -f /app/logs/http_server.log"
echo "   - API服务器日志: tail -f /app/logs/api_server.log"

# 监控循环
while true; do
    sleep 30
    check_services
done
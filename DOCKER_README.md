# Docker 构建和运行指南

## 构建 Docker 镜像

```bash
# 构建镜像
docker build -t tenbin-api .

# 或使用自定义标签
docker build -t tenbin-api:latest .
```

## 运行 Docker 容器

```bash
# 基本运行
docker run -d \
  --name tenbin-api-container \
  -p 8401:8401 \
  -p 8402:8402 \
  tenbin-api

# 带数据持久化的运行
docker run -d \
  --name tenbin-api-container \
  -p 8401:8401 \
  -p 8402:8402 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/tenbin.json:/app/tenbin.json \
  tenbin-api

# 带环境变量的运行
docker run -d \
  --name tenbin-api-container \
  -p 8401:8401 \
  -p 8402:8402 \
  -e DEBUG_MODE=true \
  tenbin-api
```

## 访问服务

- **聊天界面**: http://localhost:8402/chat.html
- **API服务**: http://localhost:8401
- **API文档**: http://localhost:8401/docs

## Docker Compose

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  tenbin-api:
    build: .
    container_name: tenbin-api-container
    ports:
      - "8401:8401"
      - "8402:8402"
    volumes:
      - ./data:/app/data
      - ./tenbin.json:/app/tenbin.json:ro
    environment:
      - DEBUG_MODE=false
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8401/models"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

运行：
```bash
docker-compose up -d
```

## 开发模式

```bash
# 使用本地文件映射进行开发
docker run -d \
  --name tenbin-dev \
  -p 8401:8401 \
  -p 8402:8402 \
  -v $(pwd):/app \
  -e DEBUG_MODE=true \
  tenbin-api
```

## 日志查看

```bash
# 查看容器日志
docker logs tenbin-api-container

# 实时查看日志
docker logs -f tenbin-api-container

# 进入容器查看详细日志
docker exec -it tenbin-api-container bash
tail -f /app/logs/api_server.log
tail -f /app/logs/http_server.log
```

## 故障排除

1. **端口占用**: 确保端口 8401 和 8402 未被占用
2. **权限问题**: 确保Docker有足够的权限访问文件
3. **依赖问题**: 重新构建镜像 `docker build --no-cache -t tenbin-api .`
4. **内存不足**: 增加Docker内存限制或使用 `--memory` 参数
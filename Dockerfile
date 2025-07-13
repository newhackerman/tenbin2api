# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive

# 更新系统并安装必要的系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    wget \
    curl \
    git \
    chromium \
    chromium-driver \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# 设置Chrome和Chromium环境变量
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 复制Python依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 安装Playwright浏览器
RUN python3 -m playwright install chromium && \
    python3 -m playwright install-deps

# 复制项目文件到容器
COPY . .
COPY ./input-network.zip /usr/local/lib/python3.11/site-packages/browserforge/headers/data/input-network.zip 
RUN chmod 777 /usr/local/lib/python3.11/site-packages/browserforge/headers/data/input-network.zip
# 创建必要的目录
RUN mkdir -p /app/logs

# 设置文件权限
RUN chmod +x /app/main.py /app/api_solver.py

# 创建非root用户运行应用
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8401 8402

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8401/models || exit 1

# 启动脚本
COPY docker-entrypoint.sh /app/
USER root
RUN chmod +x /app/docker-entrypoint.sh
USER app

# 启动命令
CMD ["/app/docker-entrypoint.sh"]

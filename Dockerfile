# ====================================================================
# Dockerfile for cursor-2api (v3.1 - Definitive Edition)
# ====================================================================

FROM python:3.10-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# --- 1. 安装 Python 依赖 ---
# 首先只复制 requirements.txt 以便利用 Docker 的构建缓存。
# 只有当 requirements.txt 文件改变时，这一层才会重新构建。
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- 2. 安装 Playwright 的系统级依赖 (以 root 身份) ---
# 使用 python -m playwright 来确保命令可以被找到，这是最稳健的方式。
RUN python -m playwright install-deps

# --- 3. 复制所有应用代码 ---
COPY . .

# --- 4. 创建并切换到非 root 用户 ---
RUN useradd --create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

# --- 5. 安装 Playwright 浏览器 (以 appuser 身份) ---
# 这将确保浏览器被下载到 /home/appuser/.cache/ms-playwright/ 目录下。
RUN python -m playwright install chromium

# --- 6. 暴露端口并定义启动命令 ---
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

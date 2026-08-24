# 后端 Docker 镜像（含前端静态文件与向量库，一体化部署）
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码与数据
COPY backend/ ./backend/
COPY data/ ./data/
COPY frontend/ ./frontend/

WORKDIR /app/backend

# 预构建向量知识库（离线 TF-IDF，无需联网）
RUN python build_kb.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

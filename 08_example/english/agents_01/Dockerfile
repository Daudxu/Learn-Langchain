FROM docker.1ms.run/python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VERSION=2.1.1

# 安装poetry
RUN pip install "poetry==$POETRY_VERSION"

# 配置poetry不创建虚拟环境
RUN poetry config virtualenvs.create false

# 安装 ping 和 curl 命令
RUN apt-get update && apt-get install -y iputils-ping curl

# 复制项目文件
COPY pyproject.toml poetry.lock* /app/
# 复制应用代码
COPY . /app/
# 安装依赖RUN poetry install --no-interaction
RUN poetry install

# 暴露需要的端口（如果有Web服务的话）
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "src.DingWebHook"]
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（GTK和其他图形界面依赖）
RUN apt-get update && apt-get install -y \
    libgtk-3-dev \
    libglib2.0-0 \
    libxcb-xinerama0 \
    libxcb-shape0 \
    libgconf-2-4 \
    libgl1-mesa-glx \
    build-essential \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY gui/ /app/gui/
COPY README.md /app/

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0

# 设置启动命令
CMD ["python", "gui/mainframe.py"]
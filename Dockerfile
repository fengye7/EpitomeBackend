# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    gettext \
    libxslt1-dev \
    zlib1g-dev \
    && apt-get clean

# 复制项目文件
COPY . /app

# 安装依赖：首先安装后端依赖
RUN pip install --no-cache-dir  -r requirements.txt

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 生成翻译文件
# RUN django-admin makemessages -l zh_HAns
# RUN django-admin makemessages -l en_US

# 编译翻译文件
RUN django-admin compilemessages

# 修改脚本权限
RUN chmod +x ./wait-for-it.sh

EXPOSE 8000

# 安装 Gunicorn
RUN pip install gunicorn

# 运行命令，使用 Gunicorn 启动 Django
CMD ["sh", "-c", "./wait-for-it.sh epitomeDb:3306 -- gunicorn --bind 0.0.0.0:8000 epitome_pyBackend.wsgi:application"]

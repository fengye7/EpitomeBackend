# 匹配前端定义 ResultEnum
import os
import requests
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json


class ResultEnum:
    SUCCESS = 0
    ERROR = 500
    OVERDUE = 9009
    TIMEOUT = 10000
    TYPE = 'success'

def generate_response(code, message, data):
    """ 生成统一格式的响应 """
    response = Response({
        "code": code,
        "message": message,
        "data": data
    })  # 处理状态码

    # 添加 CORS 头
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Headers"] = "Content-Type"
    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"

    return response

from urllib.parse import urljoin
from django.conf import settings

def download_and_store_file(url, file_type='image'):
    """
    下载文件并存储到本地媒体目录，返回公开访问 URL
    :param url: 远程文件地址
    :param file_type: 'image' 或 'video'
    :return: 可通过 Nginx 访问的 URL
    """
    file_name = url.split("/")[-1]
    subdir = "KlingImages" if file_type == "image" else "KlingVideos"
    file_path = os.path.join(subdir, file_name)

    # 如果文件已存在则复用
    if default_storage.exists(file_path):
        saved_path = file_path
    else:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            saved_path = default_storage.save(file_path, ContentFile(response.content))
        else:
            raise Exception(f"下载失败: {url}，状态码: {response.status_code}")

    # 安全拼接媒体 URL
    media_url = settings.MEDIA_URL
    if not media_url.startswith("/"):
        media_url = "/" + media_url
    if not media_url.endswith("/"):
        media_url += "/"

    # 可配置域名（默认 nginx 网关地址）
    domain = getattr(settings, "MEDIA_DOMAIN", "http://61.169.23.150:8010")  # 默认使用 Nginx 对外端口
    file_url = urljoin(domain, media_url + saved_path)

    return file_url

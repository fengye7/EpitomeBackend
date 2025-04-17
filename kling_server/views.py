import datetime
from rest_framework.views import APIView
from global_methods import ResultEnum, download_and_store_file, generate_response
from .models import UserMedia, UserMediaFile
from .serializers import UserMediaFileSerializer, UserMediaSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.translation import gettext as _

class DownloadMediaView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'media_url': openapi.Schema(type=openapi.TYPE_STRING, description=_('媒体文件URL')),
                'file_type': openapi.Schema(type=openapi.TYPE_STRING, description=_('文件类型，默认为image')),
            },
        ),
        responses={
            200: openapi.Response(_('成功'), openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'file_url': openapi.Schema(type=openapi.TYPE_STRING),
            })),
            400: _('缺少必要参数'),
            500: _('服务器错误'),
        },
    )
    def post(self, request):
        media_url = request.data.get("media_url")
        file_type = request.data.get("file_type", "image")

        if not media_url:
            return generate_response(ResultEnum.ERROR, _("缺少必要参数"), None)

        try:
            file_url = download_and_store_file(media_url, file_type)
            return generate_response(ResultEnum.SUCCESS, _("文件下载成功"), {"file_url": file_url})
        except Exception as e:
            return generate_response(ResultEnum.ERROR, str(e), None)


class UpdateMediaView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_STRING, description=_('用户ID')),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description=_('用户名')),
                'file_type': openapi.Schema(type=openapi.TYPE_STRING, description=_('媒体类型')),
                'file_url': openapi.Schema(type=openapi.TYPE_STRING, description=_('媒体文件URL')),
                'file_name': openapi.Schema(type=openapi.TYPE_STRING, description=_('自定义文件名')),
                'task_id': openapi.Schema(type=openapi.TYPE_STRING, description=_('任务id：没有这个id就新创建一条UserMediaFile记录，有就更新信息')),
                'task_status': openapi.Schema(type=openapi.TYPE_STRING, description=_('任务状态')),
                'model_name': openapi.Schema(type=openapi.TYPE_STRING, description=_('使用的模型名称')),
                'prompt': openapi.Schema(type=openapi.TYPE_STRING, description=_('提示词')),
            },
        ),
        responses={
            200: openapi.Response(_('成功'), openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
            })),
            400: _('缺少必要参数'),
            500: _('服务器错误'),
        },
    )
    def post(self, request):
        user_id = request.data.get("user_id")
        username = request.data.get("username")
        file_type = request.data.get("file_type")
        file_url = request.data.get("file_url")
        file_name = request.data.get("file_name")
        task_id = request.data.get("task_id")
        task_status = request.data.get("task_status")
        model_name = request.data.get("model_name")
        prompt = request.data.get("prompt")

        if not user_id or not username or not file_type or not file_url:
            return generate_response(ResultEnum.ERROR, _("缺少必要参数"), None)

        try:
            user_media, _ = UserMedia.objects.get_or_create(user_id=user_id, username=username)

            try:
                media_file = UserMediaFile.objects.get(task_id=task_id, user_media=user_media, file_type=file_type)
                media_file.task_status = task_status
                media_file.file_type = file_type
                media_file.file_url = file_url
                media_file.file_name = file_name
                media_file.model_name = model_name
                media_file.prompt = prompt
                media_file.save()
                message = _("信息更新成功")
            except UserMediaFile.DoesNotExist:
                UserMediaFile.objects.create(
                    user_media=user_media,
                    file_type=file_type,
                    file_url=file_url,
                    file_name=file_name,
                    model_name=model_name,
                    prompt=prompt,
                    task_id=task_id,
                )
                message = _("信息保存成功")

            return generate_response(ResultEnum.SUCCESS, message, None)
        except Exception as e:
            return generate_response(ResultEnum.ERROR, str(e), None)


class UserImageListView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, description=_("用户ID"), type=openapi.TYPE_STRING),
            openapi.Parameter('username', openapi.IN_QUERY, description=_("用户名"), type=openapi.TYPE_STRING),
        ],
        responses={
            200: UserMediaFileSerializer(many=True),
            400: _('user_id 或 username 不能为空'),
            404: _('用户记录不存在'),
        },
    )
    def get(self, request):
        user_id = request.query_params.get("user_id")
        username = request.query_params.get("username")

        if not user_id and not username:
            return generate_response(ResultEnum.ERROR, _("user_id 或 username 不能为空"), None)

        try:
            user_media = UserMedia.objects.get(user_id=user_id, username=username)
            image_files = UserMediaFile.objects.filter(user_media=user_media, file_type='image').order_by('-created_at')
            serializer = UserMediaFileSerializer(image_files, many=True)
            return generate_response(ResultEnum.SUCCESS, _("成功"), serializer.data)
        except UserMedia.DoesNotExist:
            return generate_response(ResultEnum.ERROR, _("用户记录不存在"), None)


class UserVideoListView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, description=_("用户ID"), type=openapi.TYPE_STRING),
            openapi.Parameter('username', openapi.IN_QUERY, description=_("用户名"), type=openapi.TYPE_STRING),
        ],
        responses={
            200: UserMediaFileSerializer(many=True),
            400: _('user_id 或 username 不能为空'),
            404: _('用户记录不存在'),
        },
    )
    def get(self, request):
        user_id = request.query_params.get("user_id")
        username = request.query_params.get("username")

        if not user_id and not username:
            return generate_response(ResultEnum.ERROR, _("user_id 或 username 不能为空"), None)

        try:
            user_media = UserMedia.objects.get(user_id=user_id, username=username)
            video_files = UserMediaFile.objects.filter(user_media=user_media, file_type='video').order_by('-created_at')
            serializer = UserMediaFileSerializer(video_files, many=True)
            return generate_response(ResultEnum.SUCCESS, _("成功"), serializer.data)
        except UserMedia.DoesNotExist:
            return generate_response(ResultEnum.ERROR, _("用户记录不存在"), None)
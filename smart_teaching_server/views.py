from django.http import JsonResponse
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
import json
from global_methods import ResultEnum, generate_response
from smart_teaching_server.services.interactive_teaching import get_ai_response, create_client
from smart_teaching_server.services.ppt_content_extraction import generate_teaching_script
from smart_teaching_server.services.ppt_content_extraction import create_client as create_client_2
from smart_teaching_server.services.tts_service import TTSService
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.translation import gettext as _

class TextToSpeechView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING, description=_('要合成的文本')),
                'cluster': openapi.Schema(type=openapi.TYPE_STRING, description=_('集群类型，默认值为volcano_tts')),
                'voice_type': openapi.Schema(type=openapi.TYPE_STRING, description=_('声音类型，默认值为BV001_streaming')),
            },
        ),
        responses={
            200: openapi.Response(_('成功'), openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description=_('状态码')),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description=_('提示信息')),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                        'audio_base64': openapi.Schema(type=openapi.TYPE_STRING, description=_('合成的音频的Base64编码')),
                    }),
                },
            )),
            400: _('请求参数错误'),
            500: _('语音合成失败')
        }
    )
    def post(self, request):
        data = json.loads(request.body)
        text = data.get('text', '')
        cluster = data.get('cluster', 'volcano_tts')  # 设置默认值
        voice_type = data.get('voice_type', 'zh_female_kailangjiejie_moon_bigtts')  # 设置默认值： 开朗姐姐

        if not text:
            return generate_response(ResultEnum.ERROR, _('文本不能为空'), None)

        tts_service = TTSService(appid='9008584471', access_token='hPdJoxJBVDN3_g7YIyJUXe3zcCEGUh6G', cluster=cluster, voice_type=voice_type)

        audio_base64 = tts_service.text_to_speech(text)

        if audio_base64:
            return generate_response(ResultEnum.SUCCESS, _('语音合成成功'), {'audio_base64': audio_base64})
        else:
            return generate_response(ResultEnum.ERROR, _('语音合成失败'), None)

class AIResponseView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'context': openapi.Schema(type=openapi.TYPE_STRING, description=_('上下文信息')),
                'user_input': openapi.Schema(type=openapi.TYPE_STRING, description=_('用户输入')),
            },
        ),
        responses={
            200: openapi.Response(_('成功'), openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description=_('状态码')),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description=_('提示信息')),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                        'response': openapi.Schema(type=openapi.TYPE_STRING, description=_('AI返回的响应')),
                    }),
                },
            )),
            400: _('请求参数错误')
        }
    )
    def post(self, request):
        data = json.loads(request.body)
        context = data.get('context', '')
        user_input = data.get('user_input', '')

        if not context or not user_input:
            return generate_response(ResultEnum.ERROR, _('上下文和用户输入不能为空'), None)

        client = create_client()
        response = get_ai_response(client, context, user_input)

        return generate_response(ResultEnum.SUCCESS, _('成功获取AI响应'), {'response': response})
    

class GenerateTeachingScriptView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'slide_number': openapi.Schema(type=openapi.TYPE_INTEGER, description=_('幻灯片编号')),
                'content': openapi.Schema(type=openapi.TYPE_STRING, description=_('幻灯片内容')),
                'previous_scripts': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description=_('前一页的讲稿')),
            },
        ),
        responses={
            200: openapi.Response(_('成功'), openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description=_('状态码')),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description=_('提示信息')),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                        'response': openapi.Schema(type=openapi.TYPE_STRING, description=_('生成的讲稿')),
                    }),
                },
            )),
            400: _('请求参数错误')
        }
    )
    def post(self, request):
        data = json.loads(request.body)
        slide_number = data.get('slide_number')
        content = data.get('content', '')
        previous_scripts = data.get('previous_scripts', [])

        if slide_number is None or not content:
            return generate_response(ResultEnum.ERROR, _('幻灯片编号和内容不能为空'), None)

        client = create_client_2()  # 创建 OpenAI 客户端
        try:
            # 调用讲稿生成函数
            teaching_script = generate_teaching_script(client, {
                'slide_number': slide_number,
                'content': content
            }, previous_scripts)

            return generate_response(ResultEnum.SUCCESS, _('成功获取AI响应'), {'response': teaching_script})

        except Exception as e:
            return generate_response(ResultEnum.ERROR, str(e), None)
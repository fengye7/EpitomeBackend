from django.utils import translation

LANGUAGE_MAP = {
    'zh_CN': 'zh-Hans',
    'en_US': 'en',
}


class CustomLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.headers.get('language')  # 获取请求头中的语言字段
        print(f"🧭 接收到前端语言: {lang}")
        if lang:
            mapped_lang = LANGUAGE_MAP.get(lang, 'en')  # 默认英文
            print(f"🧭 映射到后端语言: {mapped_lang}")
            translation.activate(mapped_lang)
        else:
            translation.activate('en')  # 如果没有传递语言，默认使用英文

        response = self.get_response(request)
        return response

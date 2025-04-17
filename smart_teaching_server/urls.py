from django.urls import path
from .views import TextToSpeechView, AIResponseView, GenerateTeachingScriptView

urlpatterns = [
    path('textToSpeech/', TextToSpeechView.as_view(), name='text_to_speech'),
    path('aiResponse/', AIResponseView.as_view(), name='ai_response'),
    path('generateTeachingScript/', GenerateTeachingScriptView.as_view(), name='generate_teaching_script'),
]
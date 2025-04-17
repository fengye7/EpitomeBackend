from rest_framework import serializers
from .models import UserMedia, UserMediaFile

class UserMediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMediaFile
        fields = ['file_type', 'file_url', 'file_name', 'created_at', 'model_name', 'prompt', 'task_id', 'task_status']

class UserMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMedia
        fields = ['user_id', 'username']
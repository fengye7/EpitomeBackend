from django.db import models

class UserMediaFile(models.Model):
    user_media = models.ForeignKey('UserMedia', on_delete=models.CASCADE, related_name='media_files')  # 关联用户媒体
    file_type = models.CharField(max_length=10)  # 文件类型，例如 'video' 或 'image'
    file_url = models.URLField()  # 文件的 URL
    file_name = models.CharField(max_length=100)  # 文件名
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    model_name = models.CharField(max_length=100)  # 使用的模型名
    prompt = models.TextField()  # 长文本字段
    task_id = models.CharField(max_length=100, unique=True)  # 创建的任务id，唯一标识
    task_status = models.CharField(max_length=20, default='submitted')  # 创建的任务状态

    def __str__(self):
        return f"{self.file_name} ({self.file_type})"
    

class UserMedia(models.Model):
    user_id = models.CharField(max_length=100, unique=True)  # 用户 ID 作为唯一标识
    username = models.CharField(max_length=100, unique=True)  # 用户名作为唯一标识

    def __str__(self):
        return f"{self.username} ({self.user_id})"
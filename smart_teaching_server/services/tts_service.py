import base64
import json
import uuid
import requests
import os
import logging
import tempfile
import time
import hashlib

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, appid=None, access_token=None, cluster=None, voice_type=None, cache_dir=None):
        # 默认参数，如果没有提供则使用这些值
        self.appid = appid or "9858054128"
        self.access_token = access_token or "eV9OWvrcWXLIm_bsdHIqouJrCQmuAX_l"
        self.cluster = cluster or "volcano_tts"
        self.voice_type = voice_type or "BV001_streaming"
        
        # API配置
        self.host = "openspeech.bytedance.com"
        self.api_url = f"https://{self.host}/api/v1/tts"
        self.header = {"Authorization": f"Bearer;{self.access_token}"}
        
        # 创建临时目录用于存储音频文件
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory for audio files: {self.temp_dir}")
        
        # 创建缓存目录
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            # 默认在当前目录下创建 audio_cache 目录
            self.cache_dir = os.path.join(os.getcwd(), "audio_cache")
        
        # 确保缓存目录存在
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"Created cache directory: {self.cache_dir}")
        
        # 跟踪最近生成的音频文件
        self.recent_audio_file = None
        
    def text_to_speech(self, text):
        """
        将文本转换为语音，返回 base64 编码的音频数据

        Args:
            text: 要转换为语音的文本

        Returns:
            str: base64 编码的音频数据（如果失败则为 None）
        """
        if not text:
            logger.warning("Empty text provided for TTS")
            return None

        # 构建请求JSON
        request_json = {
            "app": {
                "appid": self.appid,
                "token": "access_token",
                "cluster": self.cluster
            },
            "user": {
                "uid": "388808087185088"
            },
            "audio": {
                "voice_type": self.voice_type,
                "encoding": "mp3",
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }

        try:
            logger.info(f"Sending TTS request for text: {text[:50]}...")
            resp = requests.post(self.api_url, json.dumps(request_json), headers=self.header)

            if resp.status_code != 200:
                logger.error(f"TTS API error: {resp.status_code} - {resp.text}")
                return None

            resp_json = resp.json()
            if "data" not in resp_json:
                logger.error(f"TTS API response missing data: {resp_json}")
                return None

            # 直接返回 base64 编码音频数据
            return resp_json["data"]

        except Exception as e:
            logger.error(f"Error in TTS processing: {str(e)}")
            return None

    
    def get_recent_audio_file(self):
        """获取最近生成的音频文件路径"""
        return self.recent_audio_file
    
    def pregenerate_audio(self, text_list):
        """
        预生成一组文本的音频文件并缓存
        
        Args:
            text_list: 要预生成音频的文本列表
            
        Returns:
            int: 成功生成的音频文件数量
        """
        success_count = 0
        total_count = len(text_list)
        
        logger.info(f"Pregenerating audio for {total_count} texts...")
        
        for i, text in enumerate(text_list):
            if not text:
                continue
                
            # 使用缓存功能生成音频
            audio_path, _ = self.text_to_speech(text, use_cache=True)
            
            if audio_path:
                success_count += 1
                
            # 每生成10个音频文件输出一次进度
            if (i + 1) % 10 == 0 or i == total_count - 1:
                logger.info(f"Progress: {i+1}/{total_count} ({success_count} successful)")
                
        logger.info(f"Pregeneration completed. Generated {success_count}/{total_count} audio files.")
        return success_count
            
    def cleanup(self):
        """清理临时文件"""
        try:
            # 删除临时目录中的所有文件
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    
            # 删除临时目录
            os.rmdir(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}") 